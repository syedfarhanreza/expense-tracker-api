from datetime import date as date_type
from typing import Annotated, Literal, Optional

import models
from database import SessionLocal, engine
from fastapi import Depends, FastAPI
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session


app = FastAPI(title="Expense Tracker API")


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    username: str

    class Config:
        from_attributes = True


class TransactionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    amount: float = Field(gt=0)
    type: Literal["income", "expense"]
    category: str = Field(min_length=1, max_length=100)
    date: date_type = Field(default_factory=date_type.today)


class TransactionUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    amount: Optional[float] = Field(default=None, gt=0)
    type: Optional[Literal["income", "expense"]] = Field(default=None)
    category: Optional[str] = Field(default=None, min_length=1, max_length=100)
    date: Optional[date_type] = Field(default=None)


class TransactionResponse(BaseModel):
    id: int
    title: str
    amount: float
    type: Literal["income", "expense"]
    category: str
    date: date_type
    owner_id: int

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@app.get("/")
def read_root():
    return {"message": "Expense Tracker API is running"}
