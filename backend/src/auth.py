
from fastapi import APIRouter, Depends, HTTPException, status, Cookie, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import os
import jwt
import uuid 
from datetime import datetime, timedelta
from src.models import UserCreate, UserRead, User
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_async_session
import logging
from fastapi.responses import JSONResponse
from passlib.context import CryptContext

# Logging setup
logging.getLogger('passlib').setLevel(logging.ERROR)
logger = logging.getLogger("uvicorn")

# Security setup
pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")
security = HTTPBearer(auto_error=False) 

auth_router = APIRouter(prefix="/auth", tags=["auth"])

class SignInEmailRequest(BaseModel):
    email: str
    password: str
    callbackURL: Optional[str] = None

class SignUpEmailRequest(BaseModel):
    email: str
    password: str
    name: str
    callbackURL: Optional[str] = None

# JWT Helpers
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, os.getenv("SECRET_KEY", "your-secret-key"), algorithm="HS256")

def verify_token(token: str):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
        return payload
    except Exception as e:
        logger.error(f"Token Verification Error: {e}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency to get current authenticated user from JWT token.

    Raises:
        HTTPException: If token is invalid or missing

    Returns:
        dict: User payload from JWT token
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload

# def set_auth_cookie(response: JSONResponse, token: str):
#     response.set_cookie(
#         key="better-auth.session_token",
#         value=token,
#         httponly=True,
#         secure=False,  # Local development ke liye False
#         samesite="lax",
#         max_age=3600,
#         path="/"
#     )
def set_auth_cookie(response: JSONResponse, token: str):
    # Production check
    is_production = os.getenv("ENVIRONMENT") == "production" or "hf.space" in os.getenv("CORS_ORIGINS", "")

    response.set_cookie(
        key="better-auth.session_token",
        value=token,
        httponly=True,
        # Production mein Secure=True aur SameSite="None" hona lazmi hai
        secure=True if is_production else False, 
        samesite="none" if is_production else "lax", 
        max_age=3600,
        path="/"
    )

@auth_router.get("/get-session")
async def get_session(
    request: Request, 
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    # 1. Token extract karein (Cookie ya Header se)
    token = request.cookies.get("better-auth.session_token")
    if not token and credentials:
        token = credentials.credentials

    if not token:
        return {"user": None, "session": None, "authenticated": False}

    # 2. Token verify karein
    token_data = verify_token(token)
    if not token_data:
        return {"user": None, "session": None, "authenticated": False}

    # Better Auth ko ISO format mein 'Z' (UTC) ke sath time chahiye hota hai
    now_iso = datetime.utcnow().isoformat() + "Z"
    expiry_iso = (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"

    # 3. Final response format (Strictly for Better Auth Client)
    return {
        "user": {
            "id": str(token_data.get("sub")), 
            "email": token_data.get("email"),
            "name": token_data.get("email", "").split('@')[0],
            "emailVerified": True,
            "createdAt": now_iso,
            "updatedAt": now_iso,
        },
        "session": {
            "id": str(uuid.uuid4()),
            "userId": str(token_data.get("sub")),
            "expiresAt": expiry_iso,
            "token": token,  # Token yahan hona lazmi hai
            "createdAt": now_iso,
            "updatedAt": now_iso,
        },
        "authenticated": True
    }

@auth_router.post("/sign-in/email")
async def sign_in_email(request: SignInEmailRequest, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user or not pwd_context.verify(request.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    
    now_iso = datetime.utcnow().isoformat() + "Z"
    expiry_iso = (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"

    response_data = {
        "user": {"id": str(user.id), "email": user.email, "name": user.name},
        "session": {
            "id": str(uuid.uuid4()),
            "userId": str(user.id),
            "expiresAt": expiry_iso,
            "token": access_token
        },
        "token": access_token
    }
    
    response = JSONResponse(content=response_data)
    set_auth_cookie(response, access_token)
    return response

@auth_router.post("/sign-up/email")
async def sign_up_email(request: SignUpEmailRequest, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = pwd_context.hash(request.password)
    db_user = User(email=request.email, name=request.name, password=hashed_password)
    
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)

    access_token = create_access_token(data={"sub": str(db_user.id), "email": db_user.email})
    
    now_iso = datetime.utcnow().isoformat() + "Z"
    expiry_iso = (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"

    response_data = {
        "user": {"id": str(db_user.id), "email": db_user.email, "name": db_user.name},
        "session": {
            "id": str(uuid.uuid4()),
            "userId": str(db_user.id),
            "expiresAt": expiry_iso,
            "token": access_token
        },
        "token": access_token
    }
    
    response = JSONResponse(content=response_data)
    set_auth_cookie(response, access_token)
    return response

@auth_router.post("/sign-out")
async def sign_out():
    response = JSONResponse(content={"message": "Logged out"})
    response.delete_cookie(key="better-auth.session_token", path="/")
    return response