import pytest
from app.models.user import User


def test_user_creation():
    user = User(email="test@example.com", password_hash="hashed")
    assert user.email == "test@example.com"
    assert user.password_hash == "hashed"


def test_user_id_is_uuid_format():
    import uuid
    test_id = str(uuid.uuid4())
    user = User(id=test_id, email="test@example.com", password_hash="hashed")
    assert isinstance(uuid.UUID(user.id), uuid.UUID)
    assert user.id == test_id


