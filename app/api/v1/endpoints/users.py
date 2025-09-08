from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.api import deps
from app.core.auth import get_current_user
from app.models.user import UserRole

router = APIRouter()

@router.post("/", response_model=schemas.User)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    user = crud.user.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = crud.user.create(db, obj_in=user_in)
    return user

@router.get("/", response_model=List[schemas.User])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role == UserRole.ADMIN:
        users = crud.user.get_multi(db, skip=skip, limit=limit)
    elif current_user.role == UserRole.MANAGER:
        users = db.query(models.User).filter(models.User.department == current_user.department).offset(skip).limit(limit).all()
    else:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return users

@router.get("/{user_id}", response_model=schemas.User)
def read_user_by_id(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(get_current_user),
):
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if current_user.role == UserRole.ADMIN:
        return user
    if current_user.role == UserRole.MANAGER and user.department == current_user.department:
        return user
    if current_user.id == user.id:
        return user
    raise HTTPException(status_code=403, detail="Not enough permissions")

@router.put("/{user_id}/role", response_model=schemas.User)
def update_user_role(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    role: UserRole,
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = role
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
