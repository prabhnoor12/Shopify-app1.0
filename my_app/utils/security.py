"""
Advanced security utility functions for HMAC, token, password, JWT, and timing-safe operations.
"""

import hmac
import hashlib
import secrets
from typing import Optional
import base64
import json
import time
import os
import jwt
from jwt import PyJWTError
import bcrypt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .. import crud, models, schemas
from ..database import get_db


def verify_hmac_signature(secret: str, message: str, signature: str) -> bool:
    """
    Verify an HMAC SHA256 signature (e.g., for Shopify webhooks).
    """
    digest = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature)


def timing_safe_compare(val1: str, val2: str) -> bool:
    """
    Timing-safe string comparison to prevent timing attacks.
    """
    return hmac.compare_digest(val1, val2)


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a secure random hex token.
    """
    return secrets.token_hex(length)


def generate_random_password(length: int = 16) -> str:
    """
    Generate a secure random password with letters, digits, and symbols.
    """
    alphabet = secrets.choice
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_"
    return "".join(secrets.choice(chars) for _ in range(length))


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    """
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against a stored hash.
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except (ValueError, TypeError):
        return False


def encode_jwt(payload: dict, secret: str, exp: int = 3600) -> str:
    """
    Encode a JWT using PyJWT.
    """
    payload_to_encode = payload.copy()
    payload_to_encode["exp"] = int(time.time()) + exp
    return jwt.encode(payload_to_encode, secret, algorithm="HS256")


def decode_jwt(token: str, secret: str) -> Optional[dict]:
    """
    Decode and verify a JWT using PyJWT.
    """
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except PyJWTError:
        return None


def create_invitation_token(
    email: str, team_id: int, expires_in: int = 86400
) -> str:
    """
    Creates a JWT for team invitations.
    """
    secret = os.getenv("SECRET_KEY", "your-default-secret")
    payload = {"email": email, "team_id": team_id}
    return encode_jwt(payload, secret, exp=expires_in)


def verify_invitation_token(token: str) -> Optional[tuple[str, int]]:
    """
    Verifies an invitation token and returns the email and team_id.
    """
    secret = os.getenv("SECRET_KEY", "your-default-secret")
    payload = decode_jwt(token, secret)
    if payload and "email" in payload and "team_id" in payload:
        return payload["email"], payload["team_id"]
    return None


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.user.User:
    """
    Decode JWT and return the current user.
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_jwt(token, os.getenv("SECRET_KEY", "your-default-secret"))
    if payload is None:
        raise credentials_exception
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    user = crud.user.get_by_email(db, email=username)
    if user is None:
        raise credentials_exception
    return user
