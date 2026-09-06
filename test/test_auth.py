from fastapi import status
from models import Transaction, User
from router.auth import bcrypt_context
from test.test_main import client
from database import SessionLocal


def remove_test_user():
    db = SessionLocal()
    try:
        db.query(Transaction).filter(Transaction.owner_id == 99).delete(
            synchronize_session=False
        )
        db.query(User).filter(
            (User.id == 99) | (User.username == "testuser99")
        ).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def create_test_user():
    remove_test_user()
    db = SessionLocal()
    try:
        user = User(
            id=99,
            username="testuser99",
            email="testuser99@example.com",
            hashed_password=bcrypt_context.hash("TestPassword99!"),
        )
        db.add(user)
        db.commit()
    finally:
        db.close()


def test_user_registration():
    db = SessionLocal()
    db.query(User).filter(
        (User.username == "registration_test_user")
        | (User.email == "registration_test_user@example.com")
    ).delete(synchronize_session=False)
    db.commit()
    db.close()

    request_data = {
        "username": "registration_test_user",
        "email": "registration_test_user@example.com",
        "password": "TestPassword99!",
    }

    response = client.post("/auth/register", json=request_data)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["username"] == "registration_test_user"
    assert response.json()["email"] == "registration_test_user@example.com"
    assert "hashed_password" not in response.json()

    db = SessionLocal()
    try:
        user = db.query(User).filter(
            User.username == "registration_test_user"
        ).first()
        assert user is not None
        assert user.hashed_password != "TestPassword99!"
    finally:
        db.query(User).filter(
            User.username == "registration_test_user"
        ).delete()
        db.commit()
        db.close()


def test_user_login():
    create_test_user()

    response = client.post(
        "/auth/login",
        data={
            "username": "testuser99",
            "password": "TestPassword99!",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]
