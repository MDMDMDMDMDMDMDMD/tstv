from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.api import deps
from app.core.auth import get_current_user
from app.core.config import settings
from app.models.file import FileVisibility
from app.models.user import UserRole
import minio
import uuid

router = APIRouter()

minio_client = minio.Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=False,
)

@router.post("/upload", response_model=schemas.File)
def upload_file(
    *,
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(...),
    visibility: FileVisibility,
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role == UserRole.USER:
        if file.content_type not in ["application/pdf"]:
            raise HTTPException(status_code=400, detail="Only PDF files are allowed for USER role")
        if file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds the 10MB limit for USER role")
        if visibility != FileVisibility.PRIVATE:
            raise HTTPException(status_code=403, detail="USER role can only create private files")

    if current_user.role == UserRole.MANAGER:
        if file.size > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds the 50MB limit for MANAGER role")

    if current_user.role == UserRole.ADMIN:
        if file.size > 100 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds the 100MB limit for ADMIN role")

    s3_key = f"{uuid.uuid4()}-{file.filename}"
    minio_client.put_object(
        settings.MINIO_BUCKET,
        s3_key,
        file.file,
        file.size,
        content_type=file.content_type,
    )

    db_file = models.File(
        filename=file.filename,
        s3_key=s3_key,
        owner_id=current_user.id,
        visibility=visibility,
        department=current_user.department,
        size=file.size,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    from app.worker.tasks import extract_metadata
    extract_metadata.delay(db_file.id)

    return db_file

@router.get("/{file_id}", response_model=schemas.File)
def read_file(
    file_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(get_current_user),
):
    file = crud.file.get(db, id=file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    if current_user.role == UserRole.ADMIN:
        return file
    if file.visibility == FileVisibility.PUBLIC:
        return file
    if file.visibility == FileVisibility.DEPARTMENT:
        if current_user.role == UserRole.MANAGER:
            return file
        if current_user.department == file.department:
            return file
    if file.owner_id == current_user.id:
        return file

    raise HTTPException(status_code=403, detail="Not enough permissions")

@router.get("/{file_id}/download")
def download_file(
    file_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(get_current_user),
):
    file = crud.file.get(db, id=file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    if current_user.role == UserRole.ADMIN:
        pass
    elif file.visibility == FileVisibility.PUBLIC:
        pass
    elif file.visibility == FileVisibility.DEPARTMENT:
        if current_user.role != UserRole.MANAGER and current_user.department != file.department:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    elif file.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    file.downloads += 1
    db.commit()

    try:
        response = minio_client.get_object(settings.MINIO_BUCKET, file.s3_key)
        return StreamingResponse(response.stream(32 * 1024), media_type="application/octet-stream")
    finally:
        response.close()
        response.release_conn()

@router.delete("/{file_id}", response_model=schemas.File)
def delete_file(
    file_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(get_current_user),
):
    file = crud.file.get(db, id=file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    if current_user.role == UserRole.ADMIN:
        pass
    elif current_user.role == UserRole.MANAGER and current_user.department == file.department:
        pass
    elif file.owner_id == current_user.id:
        pass
    else:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    minio_client.remove_object(settings.MINIO_BUCKET, file.s3_key)
    crud.file.remove(db, id=file_id)
    return file

@router.get("/", response_model=List[schemas.File])
def list_files(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(get_current_user),
    department: str = None,
):
    query = db.query(models.File)
    if current_user.role == UserRole.ADMIN:
        if department:
            query = query.filter(models.File.department == department)
    elif current_user.role == UserRole.MANAGER:
        if department and department != current_user.department:
            # Managers can see files from other departments
             query = query.filter(models.File.department == department)
        else:
            # by default, show files from their own department and public files
            query = query.filter(
                (models.File.department == current_user.department) | (models.File.visibility == FileVisibility.PUBLIC)
            )
    else: # USER
        query = query.filter(
            (models.File.owner_id == current_user.id) |
            (models.File.visibility == FileVisibility.PUBLIC) |
            ((models.File.visibility == FileVisibility.DEPARTMENT) & (models.File.department == current_user.department))
        )

    return query.all()
