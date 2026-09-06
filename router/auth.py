from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from database import SessionLocal
from models import User


router = APIRouter()

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
OAuth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/login")

SECRET_KEY = "00b18e536d3f8e68a66ddd33595c07dcebbc127edfa344f1accc7de8c55d4c89"
ALGORITHM = "HS256"


class CreateUser(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=3)


def authenticate_user(username, password, db):
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        return False
    if bcrypt_context.verify(password, user.hashed_password):
        return user
    return False


def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    encode = {"sub": username, "id": user_id}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: Annotated[str, Depends(OAuth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
            )
        return {"username": username, "id": user_id}
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
        )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@router.post("/register", status_code=201)
def register_user(db: db_dependency, new_user: CreateUser):
    existing_user = db.query(User).filter(
        (User.username == new_user.username) | (User.email == new_user.email)
    ).first()
    if existing_user is not None:
        raise HTTPException(
            status_code=409,
            detail="Username or email already exists",
        )

    user_model = User(
        email=new_user.email,
        username=new_user.username,
        hashed_password=bcrypt_context.hash(new_user.password),
    )
    db.add(user_model)
    db.commit()
    db.refresh(user_model)

    return {
        "id": user_model.id,
        "email": user_model.email,
        "username": user_model.username,
    }


@router.post("/login")
def login_user(
    db: db_dependency,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"message": "Invalid username or password"},
        )

    token = create_access_token(
        user.username,
        user.id,
        timedelta(minutes=30),
    )
    return {
        "access_token": token,
        "token_type": "bearer",
    }
