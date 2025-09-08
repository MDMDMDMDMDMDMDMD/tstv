from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.db.session import get_db
from app.core.auth import create_access_token, get_current_user

router = APIRouter()

@router.post("/login", response_model=schemas.Token)
def login(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    user = crud.user.authenticate(
        db, username=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "access_token": create_access_token(data={"sub": user.username}),
        "token_type": "bearer",
    }

@router.post("/create-admin", response_model=schemas.User, status_code=201)
def create_first_admin(
    *,
    db: Session = Depends(get_db),
    user_in: schemas.UserCreate,
):
    if crud.user.get_multi(db):
        raise HTTPException(status_code=400, detail="Admin user already exists. Cannot create another unauthenticated admin.")
    if user_in.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=400, detail="Only ADMIN role can be created via this endpoint.")
    
    user = crud.user.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(status_code=400, detail="The user with this username already exists in the system.")
    
    user = crud.user.create(db, obj_in=user_in)
    return user

@router.get("/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user
