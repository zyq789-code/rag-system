from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.exceptions import AppError
from core.security import hash_password, verify_password, create_access_token
from models.user import User
from repositories.user import UserRepository
from schemas.auth import RegisterRequest, LoginRequest, TokenResponse

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    if await repo.get_by_username(data.username):
        raise AppError("用户名已存在", 400)
    user = User(username=data.username, password_hash=hash_password(data.password))
    await repo.create(user)
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, username=user.username)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get_by_username(data.username)
    # 统一报错信息，不泄露"用户名是否存在"
    if not user or not verify_password(data.password, user.password_hash):
        raise AppError("用户名或密码错误", 401)
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, username=user.username)
