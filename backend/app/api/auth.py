from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.auth import verify_password, hash_password, create_access_token, get_current_user
from app.core.database import get_db
from app.models.user import UserORM
import uuid

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str
    email: str


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(UserORM).where(UserORM.email == req.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = UserORM(
        id=str(uuid.uuid4()),
        email=req.email,
        name=req.name,
        password_hash=hash_password(req.password),
    )
    db.add(user)
    await db.commit()

    token = create_access_token({"sub": user.email})
    return TokenResponse(access_token=token, user_id=user.id, name=user.name, email=user.email)


@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserORM).where(UserORM.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": user.email})
    return TokenResponse(access_token=token, user_id=user.id, name=user.name, email=user.email)


@router.post("/login/json", response_model=TokenResponse)
async def login_json(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """JSON body login (for frontend convenience)."""
    result = await db.execute(select(UserORM).where(UserORM.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": user.email})
    return TokenResponse(access_token=token, user_id=user.id, name=user.name, email=user.email)


@router.get("/me")
async def me(user: UserORM = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "name": user.name}
