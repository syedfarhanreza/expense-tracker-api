from datetime import date as date_type
from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Transaction
from router.auth import get_current_user


router = APIRouter()


class CreateTransaction(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    amount: float = Field(gt=0)
    type: Literal["income", "expense"]
    category: str = Field(min_length=1, max_length=100)
    date: date_type = Field(default_factory=date_type.today)


class UpdateTransaction(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    amount: Optional[float] = Field(default=None, gt=0)
    type: Optional[Literal["income", "expense"]] = Field(default=None)
    category: Optional[str] = Field(default=None, min_length=1, max_length=100)
    date: Optional[date_type] = Field(default=None)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


def get_user_transaction(db, user, transaction_id):
    return db.query(Transaction).filter(
        Transaction.owner_id == user.get("id"),
        Transaction.id == transaction_id,
    ).first()


@router.post("", status_code=201)
def create_transaction(
    user: user_dependency,
    db: db_dependency,
    new_transaction: CreateTransaction,
):
    transaction_model = Transaction(
        **new_transaction.model_dump(),
        owner_id=user.get("id"),
    )
    db.add(transaction_model)
    db.commit()
    db.refresh(transaction_model)
    return transaction_model


@router.get("")
def read_transactions(user: user_dependency, db: db_dependency):
    return db.query(Transaction).filter(
        Transaction.owner_id == user.get("id")
    ).all()


@router.get("/filter")
def filter_transactions(
    user: user_dependency,
    db: db_dependency,
    type: Optional[Literal["income", "expense"]] = None,
    category: Optional[str] = None,
    minimum_amount: Optional[float] = None,
    maximum_amount: Optional[float] = None,
):
    transactions = db.query(Transaction).filter(
        Transaction.owner_id == user.get("id")
    )

    if type is not None:
        transactions = transactions.filter(Transaction.type == type)
    if category is not None:
        transactions = transactions.filter(Transaction.category == category)
    if minimum_amount is not None:
        transactions = transactions.filter(
            Transaction.amount >= minimum_amount
        )
    if maximum_amount is not None:
        transactions = transactions.filter(
            Transaction.amount <= maximum_amount
        )

    return transactions.all()


@router.get("/{transaction_id}")
def read_transaction(
    user: user_dependency,
    db: db_dependency,
    transaction_id: int,
):
    transaction = get_user_transaction(db, user, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@router.put("/{transaction_id}")
def update_transaction(
    user: user_dependency,
    db: db_dependency,
    transaction_id: int,
    update_data: UpdateTransaction,
):
    transaction = get_user_transaction(db, user, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(transaction, key, value)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.delete("/{transaction_id}")
def delete_transaction(
    user: user_dependency,
    db: db_dependency,
    transaction_id: int,
):
    transaction = get_user_transaction(db, user, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(transaction)
    db.commit()
    return JSONResponse(
        status_code=200,
        content={"message": "Transaction deleted successfully"},
    )
