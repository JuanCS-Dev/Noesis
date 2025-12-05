"""HITL Backend - Authentication Module.

JWT authentication, 2FA, and user management endpoints.
"""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict

import pyotp
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

from .database import db
from .models import (
    Token,
    TokenData,
    TwoFactorSetup,
    UserCreate,
    UserInDB,
    UserRole,
)

logger = logging.getLogger(__name__)

# Security Configuration
SECRET_KEY = secrets.token_urlsafe(32)  # In production, load from env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# Router
router = APIRouter(prefix="/api/auth", tags=["auth"])


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password."""
    return pwd_context.hash(password)


def create_access_token(
    data: dict, expires_delta: timedelta | None = None
) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token."""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = data.copy()
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

        TokenData(username=username, role=payload.get("role"))

    except JWTError as e:
        raise credentials_exception from e

    user = db.get_user(username=username)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


async def get_current_active_analyst(
    current_user: UserInDB = Depends(get_current_user),
) -> UserInDB:
    """Require analyst or admin role."""
    if current_user.role not in [UserRole.ANALYST, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user


async def get_current_admin(
    current_user: UserInDB = Depends(get_current_user),
) -> UserInDB:
    """Require admin role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.post("/register", response_model=Dict[str, str])
async def register_user(
    user_data: UserCreate,
    current_admin: UserInDB = Depends(get_current_admin),
) -> Dict[str, str]:
    """Register new user (admin only)."""
    if db.get_user(user_data.username):
        raise HTTPException(status_code=400, detail="Username already registered")

    new_user = UserInDB(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role,
        hashed_password=get_password_hash(user_data.password),
        is_active=True,
        created_at=datetime.now(),
    )

    db.add_user(new_user)

    db.audit(
        "USER_CREATED",
        current_admin.username,
        {"new_user": user_data.username, "role": user_data.role.value},
    )

    logger.info("User registered: %s (role: %s)", user_data.username, user_data.role.value)

    return {"message": "User registered successfully", "username": user_data.username}


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    """Login and get JWT tokens."""
    user = db.get_user(form_data.username)

    if not user or not verify_password(form_data.password, user.hashed_password):
        db.audit("LOGIN_FAILED", form_data.username, {"reason": "invalid_credentials"})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    if user.is_2fa_enabled:
        temp_token = create_access_token(
            data={"sub": user.username, "role": user.role.value, "requires_2fa": True},
            expires_delta=timedelta(minutes=5),
        )
        return Token(access_token=temp_token, refresh_token="", requires_2fa=True)

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_refresh_token(data={"sub": user.username})

    user.last_login = datetime.now()

    db.audit("LOGIN_SUCCESS", user.username, {"ip": "unknown"})

    logger.info("User logged in: %s", user.username)

    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/2fa/setup", response_model=TwoFactorSetup)
async def setup_2fa(
    current_user: UserInDB = Depends(get_current_user),
) -> TwoFactorSetup:
    """Setup 2FA for user."""
    secret = pyotp.random_base32()

    totp = pyotp.TOTP(secret)
    qr_url = totp.provisioning_uri(
        name=current_user.email, issuer_name="Reactive Fabric HITL"
    )

    backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]

    current_user.totp_secret = secret
    current_user.is_2fa_enabled = False

    db.audit("2FA_SETUP", current_user.username, {"status": "initiated"})

    logger.info("2FA setup initiated for user: %s", current_user.username)

    return TwoFactorSetup(secret=secret, qr_code_url=qr_url, backup_codes=backup_codes)


@router.post("/2fa/verify")
async def verify_2fa(
    code: str,
    current_user: UserInDB = Depends(get_current_user),
) -> Dict[str, str]:
    """Verify 2FA code."""
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="2FA not set up")

    totp = pyotp.TOTP(current_user.totp_secret)

    if not totp.verify(code, valid_window=1):
        db.audit("2FA_VERIFY_FAILED", current_user.username, {"reason": "invalid_code"})
        raise HTTPException(status_code=401, detail="Invalid 2FA code")

    current_user.is_2fa_enabled = True

    db.audit("2FA_ENABLED", current_user.username, {})

    logger.info("2FA enabled for user: %s", current_user.username)

    return {"message": "2FA verified and enabled"}


@router.get("/me", response_model=Dict[str, Any])
async def get_current_user_info(
    current_user: UserInDB = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get current user info."""
    return {
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "is_2fa_enabled": current_user.is_2fa_enabled,
        "last_login": (
            current_user.last_login.isoformat() if current_user.last_login else None
        ),
    }
