from datetime import date

from fastapi import status
from models import Transaction
from router.auth import get_current_user
from test.test_main import app, client
from database import SessionLocal


def override_get_current_user():
    return {
        "id": 1,
        "username": "testuser",
    }


app.dependency_overrides[get_current_user] = override_get_current_user


def create_test_transaction(transaction_id=99):
    db = SessionLocal()
    try:
        db.query(Transaction).filter(
            Transaction.id == transaction_id
        ).delete()
        transaction = Transaction(
            id=transaction_id,
            title="Test Transaction",
            amount=150,
            type="expense",
            category="Food",
            date=date.today(),
            owner_id=1,
        )
        db.add(transaction)
        db.commit()
    finally:
        db.close()


def test_get_transactions():
    create_test_transaction()

    response = client.get("/transactions")

    assert response.status_code == status.HTTP_200_OK
    assert any(
        transaction["title"] == "Test Transaction"
        for transaction in response.json()
    )


def test_get_specific_transaction():
    create_test_transaction()

    response = client.get("/transactions/99")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == 99


def test_create_transaction():
    request_data = {
        "title": "New Transaction",
        "amount": 250,
        "type": "income",
        "category": "Salary",
        "date": str(date.today()),
    }
    response = client.post("/transactions", json=request_data)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["title"] == "New Transaction"
    assert response.json()["owner_id"] == 1


def test_update_transaction():
    create_test_transaction()
    request_data = {
        "title": "Updated Transaction",
        "amount": 300,
    }

    response = client.put("/transactions/99", json=request_data)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["title"] == "Updated Transaction"
    assert response.json()["amount"] == 300


def test_delete_transaction():
    create_test_transaction()

    response = client.delete("/transactions/99")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "message": "Transaction deleted successfully"
    }
