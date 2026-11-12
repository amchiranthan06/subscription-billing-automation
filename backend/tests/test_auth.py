import os
import sys
import unittest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base
from app.models.models import User
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token

class TestUserAuthentication(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        self.Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = self.Session()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_password_hashing_and_verification(self):
        raw_password = "SecurePassword123!"
        hashed = hash_password(raw_password)
        
        self.assertNotEqual(raw_password, hashed)
        self.assertTrue(verify_password(raw_password, hashed))
        self.assertFalse(verify_password("WrongPassword!", hashed))

    def test_jwt_token_creation_and_decoding(self):
        user_data = {"sub": "user_12345", "email": "test@example.com", "role": "user"}
        token = create_access_token(data=user_data)
        
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 20)

        decoded = decode_access_token(token)
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded["sub"], "user_12345")
        self.assertEqual(decoded["email"], "test@example.com")
        self.assertEqual(decoded["role"], "user")

    def test_user_creation_in_db(self):
        user = User(
            name="Alice Smith",
            email="alice@example.com",
            hashed_password=hash_password("SuperSecret123"),
            role="user"
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        self.assertIsNotNone(user.id)
        fetched = self.db.query(User).filter(User.email == "alice@example.com").first()
        self.assertEqual(fetched.name, "Alice Smith")
        self.assertTrue(verify_password("SuperSecret123", fetched.hashed_password))

if __name__ == "__main__":
    unittest.main()
