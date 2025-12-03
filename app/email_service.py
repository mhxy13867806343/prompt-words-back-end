import random
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings
from app.redis_client import get_redis

async def generate_code() -> str:
    return str(random.randint(100000, 999999))

async def send_verification_code(email: str, code: str):
    message = MIMEMultipart()
    message["From"] = settings.SMTP_FROM
    message["To"] = email
    message["Subject"] = "验证码"
    
    body = f"您的验证码是: {code}，有效期5分钟。"
    message.attach(MIMEText(body, "plain"))
    
    await aiosmtplib.send(
        message,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        start_tls=True,
    )

async def send_code_to_email(email: str) -> str:
    code = await generate_code()
    redis = await get_redis()
    await redis.setex(f"email_code:{email}", 300, code)  # 5分钟过期
    await send_verification_code(email, code)
    return code

async def verify_code(email: str, code: str) -> bool:
    redis = await get_redis()
    stored_code = await redis.get(f"email_code:{email}")
    if stored_code and stored_code == code:
        await redis.delete(f"email_code:{email}")
        return True
    return False
