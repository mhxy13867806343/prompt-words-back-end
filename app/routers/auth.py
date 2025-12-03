from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.database import get_db
from app.models import User
from app.schemas import (
    UserRegister, UserLogin, EmailBind, SendCodeRequest, ResetPassword,
    ResponseModel, TokenResponse, UserResponse
)
from app.auth import verify_password, get_password_hash, create_access_token, get_current_user
from app.email_service import send_code_to_email, verify_code
from app.redis_client import get_redis

router = APIRouter(prefix="/auth", tags=["认证"])

@router.post("/register", response_model=ResponseModel)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        return ResponseModel(code=400, msg="用户名已存在")
    
    new_user = User(
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        state=0
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    access_token = create_access_token(data={"sub": new_user.id})
    user_response = UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        state=new_user.state,
        created_at=new_user.created_at
    )
    
    return ResponseModel(
        data=TokenResponse(access_token=access_token, user=user_response).model_dump(by_alias=True)
    )

@router.post("/login", response_model=ResponseModel)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        return ResponseModel(code=400, msg="用户名或密码错误")
    
    access_token = create_access_token(data={"sub": user.id})
    user_response = UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        state=user.state,
        created_at=user.created_at
    )
    
    return ResponseModel(
        data=TokenResponse(access_token=access_token, user=user_response).model_dump(by_alias=True)
    )

@router.post("/send-code", response_model=ResponseModel)
async def send_code(request: SendCodeRequest):
    try:
        await send_code_to_email(request.email)
        return ResponseModel(msg="验证码已发送")
    except Exception as e:
        return ResponseModel(code=500, msg=f"发送失败: {str(e)}")

@router.post("/bind-email", response_model=ResponseModel)
async def bind_email(
    request: EmailBind,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not await verify_code(request.email, request.code):
        return ResponseModel(code=400, msg="验证码错误或已过期")
    
    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        return ResponseModel(code=400, msg="该邮箱已被绑定")
    
    await db.execute(
        update(User).where(User.id == current_user.id).values(email=request.email, state=1)
    )
    await db.commit()
    
    return ResponseModel(msg="邮箱绑定成功")

@router.post("/reset-password", response_model=ResponseModel)
async def reset_password(request: ResetPassword, db: AsyncSession = Depends(get_db)):
    if not await verify_code(request.email, request.code):
        return ResponseModel(code=400, msg="验证码错误或已过期")
    
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()
    
    if not user:
        return ResponseModel(code=404, msg="该邮箱未绑定任何账户")
    
    await db.execute(
        update(User).where(User.id == user.id).values(hashed_password=get_password_hash(request.new_password))
    )
    await db.commit()
    
    return ResponseModel(msg="密码重置成功")

@router.post("/logout", response_model=ResponseModel)
async def logout(current_user: User = Depends(get_current_user)):
    # Token 在客户端清除即可
    return ResponseModel(msg="退出成功")

@router.get("/user", response_model=ResponseModel)
async def get_user(current_user: User = Depends(get_current_user)):
    user_response = UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        state=current_user.state,
        created_at=current_user.created_at
    )
    return ResponseModel(data=user_response.model_dump(by_alias=True))
