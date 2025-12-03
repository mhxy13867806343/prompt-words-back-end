from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime

class ResponseModel(BaseModel):
    code: int = 200
    data: Any = None
    msg: str = "成功"

def to_camel(string: str) -> str:
    components = string.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class EmailBind(BaseModel):
    email: EmailStr
    code: str

class SendCodeRequest(BaseModel):
    email: EmailStr

class ResetPassword(BaseModel):
    email: EmailStr
    code: str
    new_password: str = Field(..., min_length=6)

class UserResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    
    id: int
    username: str
    email: Optional[str]
    state: int
    created_at: datetime

class TokenResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class PromptCreate(BaseModel):
    title: str = Field(..., max_length=200)
    content: str = Field(..., max_length=30000)

class PromptUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = Field(None, max_length=30000)

class PromptResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    
    id: int
    user_id: int
    title: str
    content: str
    state: int
    view_count: int
    like_count: int
    favorite_count: int
    created_at: datetime
    updated_at: Optional[datetime]
    is_liked: bool = False
    is_favorited: bool = False

class PromptListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    
    list: List[PromptResponse]
    total: int
    page: int
    page_size: int

class StatsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    
    total_prompts: int
    total_views: int
