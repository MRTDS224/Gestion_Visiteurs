from datetime import datetime, timedelta, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from passlib.hash import bcrypt
import secrets

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String(50), nullable=True)
    prenom = Column(String(50), nullable=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column("password_hash", String(128), nullable=False)
    structure = Column(String(100), nullable=False)
    role = Column(String(20), default="utilisateur", nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    
    shares_sent     = relationship(
        "VisitorShare",
        back_populates="shared_by",
        foreign_keys="VisitorShare.shared_by_user_id",
    )
    shares_received = relationship(
        "VisitorShare",
        back_populates="shared_with",
        foreign_keys="VisitorShare.shared_with_user_id",
    )

    def __repr__(self):
        return f"<User(id={self.id!r}, email={self.email!r}, structure={self.structure!r})>"

    def set_password(self, password: str) -> None:
        """
        Hash and store the user’s password.
        """
        self.password_hash = bcrypt.hash(password)

    def verify_password(self, password: str) -> bool:
        """
        Verify a plaintext password against the stored hash.
        """
        return bcrypt.verify(password, self.password_hash)

# Durée de validité du token (ici 1 heure)
RESET_TOKEN_EXPIRY = timedelta(hours=1)

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(64), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    def __init__(self, user_id: int):
        self.user_id = user_id
        # Génère un token URL-safe de 32 bytes (~43 chars)
        self.token = secrets.token_urlsafe(32)
        self.expires_at = datetime.now(timezone.utc) + RESET_TOKEN_EXPIRY
        
    def is_expired(self):
        return datetime.now(timezone.utc) > self.expires_at
