from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from .models.user import TokenData, UserDisplay, UserCreate
from .database import UserDB
from sqlalchemy.orm import Session
from .database import get_db

# --- Configuration --- #

# IMPORTANT: Change this to a strong, random key and store it securely (e.g., env var)!
# You can generate one with: openssl rand -hex 32
SECRET_KEY = "your-secret-key-here-please-change-me"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Access token lifetime

# Password Hashing Context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 Scheme
# "tokenUrl" should match the path of your token-issuing endpoint (e.g., /login, /auth/token)
# We'll create an endpoint at /token later
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Password Utilities --- #

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)

# --- JWT Utilities --- #

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- User specific database functions (moved from database.py) --- #

def get_user_by_email(db: Session, email: str) -> UserDB | None:
    """Fetches a user from the database by their email address."""
    return db.query(UserDB).filter(UserDB.email == email).first()

def create_user(db: Session, user: UserCreate) -> UserDB:
    """Creates a new user in the database."""
    hashed_password = get_password_hash(user.password) # Uses local get_password_hash
    db_user = UserDB(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Authentication --- #

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    if not user.is_active: # Optional: Check if the user is active
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

async def get_current_active_user(current_user: UserDB = Depends(get_current_user)) -> UserDB:
    # This is a convenience dependency if you want to ensure the user is active
    # get_current_user already checks for active status in this implementation,
    # but separating it can be useful if you have different states of "current_user"
    # vs "current_active_user" in more complex scenarios.
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
