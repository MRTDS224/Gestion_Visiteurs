from datetime import datetime, timedelta, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    LargeBinary,
    Text,
    func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from passlib.hash import argon2
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
        foreign_keys="[VisitorShare.shared_by_user_id]",
    )
    shares_received = relationship(
        "VisitorShare",
        back_populates="shared_with",
        foreign_keys="[VisitorShare.shared_with_user_id]",
    )

    def __repr__(self):
        return f"<User(id={self.id!r}, email={self.email!r}, structure={self.structure!r})>"

    def set_password(self, password: str) -> None:
        """
        Hash and store the user’s password.
        """
        self.password_hash = argon2.hash(password)

    def verify_password(self, password: str) -> bool:
        """
        Verify a plaintext password against the stored hash.
        """
        return argon2.verify(password, self.password_hash)

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

class VisitorShare(Base):
    __tablename__ = "visitor_shares"
    id                   = Column(Integer, primary_key=True)
    visitor_id           = Column(Integer, nullable=False, index=True)
    shared_by_user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    shared_with_user_id  = Column(Integer, ForeignKey("users.id"), nullable=False)
    place_of_birth       = Column(String, nullable=False)
    phone_number         = Column(String, nullable=False)
    motif                = Column(Text)
    image_data           = Column(LargeBinary, nullable=False)
    shared_at            = Column(DateTime(timezone=True), server_default=func.now())
    status               = Column(String, default="active", nullable=False)

    shared_by  = relationship("User", back_populates="shares_sent",
                              foreign_keys=[shared_by_user_id])
    shared_with = relationship("User", back_populates="shares_received",
                               foreign_keys=[shared_with_user_id])