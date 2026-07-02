from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from fastapi import HTTPException
from sqlalchemy.exc import OperationalError

from app.models.user import User
from app.services.auth_service import authenticate_user, create_user_with_default_store
from app.core.security import hash_password


class AuthServiceTest(unittest.TestCase):
    def test_signup_creates_user_and_default_store(self) -> None:
        db = MagicMock()
        db.scalar.return_value = None

        user = create_user_with_default_store(db, "Seller@Example.com", "password123")

        self.assertEqual(user.email, "seller@example.com")
        added_records = db.add_all.call_args.args[0]
        self.assertEqual(len(added_records), 2)
        created_user, created_store = added_records
        self.assertEqual(created_user.email, "seller@example.com")
        self.assertEqual(created_store.name, "My Amazon Store")
        self.assertEqual(created_store.marketplace, "amazon_in")
        self.assertIs(created_store.user, created_user)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(user)

    def test_duplicate_signup_returns_expected_error(self) -> None:
        db = MagicMock()
        db.scalar.return_value = User(
            email="seller@example.com",
            password_hash="hash",
        )

        with self.assertRaises(HTTPException) as context:
            create_user_with_default_store(db, "seller@example.com", "password123")

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("already exists", context.exception.detail)

    def test_signup_db_connection_failure_returns_safe_error(self) -> None:
        db = MagicMock()
        db.scalar.side_effect = OperationalError("SELECT", {}, Exception("boom"))

        with self.assertRaises(HTTPException) as context:
            create_user_with_default_store(db, "seller@example.com", "password123")

        self.assertEqual(context.exception.status_code, 503)
        self.assertIn("database", context.exception.detail.lower())

    def test_login_works(self) -> None:
        db = MagicMock()
        db.scalar.return_value = User(
            email="seller@example.com",
            password_hash=hash_password("password123"),
        )

        user = authenticate_user(db, "seller@example.com", "password123")

        self.assertEqual(user.email, "seller@example.com")

    def test_login_invalid_credentials_fails_cleanly(self) -> None:
        db = MagicMock()
        db.scalar.return_value = User(
            email="seller@example.com",
            password_hash=hash_password("password123"),
        )

        with self.assertRaises(HTTPException) as context:
            authenticate_user(db, "seller@example.com", "wrong-password")

        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("invalid email or password", context.exception.detail.lower())


if __name__ == "__main__":
    unittest.main()
