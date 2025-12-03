from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_, or_
from typing import Optional
from app.database import get_db
from app.models import User, Prompt, PromptView, PromptLike, PromptFavorite
from app.schemas import (
    PromptCreate, PromptUpdate, ResponseModel, PromptResponse, PromptListResponse, StatsResponse
)
from app.auth import get_current_user, get_optional_user
from app.redis_client import get_redis

router = APIRouter(prefix="/prompts", tags=["提示词"])

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host

@router.post("", response_model=ResponseModel)
async def create_prompt(
    prompt_data: PromptCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    new_prompt = Prompt(
        user_id=current_user.id,
        title=prompt_data.title,
        content=prompt_data.content
    )
    db.add(new_prompt)
    await db.commit()
    await db.refresh(new_prompt)
    
    response = PromptResponse(
        id=new_prompt.id,
        user_id=new_prompt.user_id,
        title=new_prompt.title,
        content=new_prompt.content,
        state=new_prompt.state,
        view_count=new_prompt.view_count,
        like_count=new_prompt.like_count,
        favorite_count=new_prompt.favorite_count,
        created_at=new_prompt.created_at,
        updated_at=new_prompt.updated_at
    )
    
    return ResponseModel(data=response.model_dump(by_alias=True))

@router.get("", response_model=ResponseModel)
async def list_prompts(
    page: int = 1,
    pageSize: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    page_size = pageSize
    offset = (page - 1) * page_size
    
    query = select(Prompt).where(Prompt.state == 1).order_by(Prompt.created_at.desc())
    result = await db.execute(query.limit(page_size).offset(offset))
    prompts = result.scalars().all()
    
    count_result = await db.execute(select(func.count(Prompt.id)).where(Prompt.state == 1))
    total = count_result.scalar()
    
    prompt_list = []
    for prompt in prompts:
        is_liked = False
        is_favorited = False
        
        if current_user:
            like_result = await db.execute(
                select(PromptLike).where(
                    and_(PromptLike.prompt_id == prompt.id, PromptLike.user_id == current_user.id)
                )
            )
            is_liked = like_result.scalar_one_or_none() is not None
            
            fav_result = await db.execute(
                select(PromptFavorite).where(
                    and_(PromptFavorite.prompt_id == prompt.id, PromptFavorite.user_id == current_user.id)
                )
            )
            is_favorited = fav_result.scalar_one_or_none() is not None
        
        prompt_list.append(PromptResponse(
            id=prompt.id,
            user_id=prompt.user_id,
            title=prompt.title,
            content=prompt.content,
            state=prompt.state,
            view_count=prompt.view_count,
            like_count=prompt.like_count,
            favorite_count=prompt.favorite_count,
            created_at=prompt.created_at,
            updated_at=prompt.updated_at,
            is_liked=is_liked,
            is_favorited=is_favorited
        ))
    
    response = PromptListResponse(
        list=prompt_list,
        total=total,
        page=page,
        page_size=page_size
    )
    
    return ResponseModel(data=response.model_dump(by_alias=True))

@router.get("/{promptId}", response_model=ResponseModel)
async def get_prompt(
    promptId: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    prompt_id = promptId
    result = await db.execute(select(Prompt).where(and_(Prompt.id == prompt_id, Prompt.state == 1)))
    prompt = result.scalar_one_or_none()
    
    if not prompt:
        return ResponseModel(code=404, msg="提示词不存在")
    
    # 记录浏览（限IP）
    ip = get_client_ip(request)
    view_result = await db.execute(
        select(PromptView).where(and_(PromptView.prompt_id == prompt_id, PromptView.ip_address == ip))
    )
    if not view_result.scalar_one_or_none():
        new_view = PromptView(
            prompt_id=prompt_id,
            user_id=current_user.id if current_user else None,
            ip_address=ip
        )
        db.add(new_view)
        await db.execute(
            update(Prompt).where(Prompt.id == prompt_id).values(view_count=Prompt.view_count + 1)
        )
        await db.commit()
        prompt.view_count += 1
    
    is_liked = False
    is_favorited = False
    
    if current_user:
        like_result = await db.execute(
            select(PromptLike).where(
                and_(PromptLike.prompt_id == prompt_id, PromptLike.user_id == current_user.id)
            )
        )
        is_liked = like_result.scalar_one_or_none() is not None
        
        fav_result = await db.execute(
            select(PromptFavorite).where(
                and_(PromptFavorite.prompt_id == prompt_id, PromptFavorite.user_id == current_user.id)
            )
        )
        is_favorited = fav_result.scalar_one_or_none() is not None
    
    response = PromptResponse(
        id=prompt.id,
        user_id=prompt.user_id,
        title=prompt.title,
        content=prompt.content,
        state=prompt.state,
        view_count=prompt.view_count,
        like_count=prompt.like_count,
        favorite_count=prompt.favorite_count,
        created_at=prompt.created_at,
        updated_at=prompt.updated_at,
        is_liked=is_liked,
        is_favorited=is_favorited
    )
    
    return ResponseModel(data=response.model_dump(by_alias=True))

@router.put("/{promptId}", response_model=ResponseModel)
async def update_prompt(
    promptId: int,
    prompt_data: PromptUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    prompt_id = promptId
    result = await db.execute(
        select(Prompt).where(and_(Prompt.id == prompt_id, Prompt.user_id == current_user.id, Prompt.state == 1))
    )
    prompt = result.scalar_one_or_none()
    
    if not prompt:
        return ResponseModel(code=404, msg="提示词不存在或无权限")
    
    update_data = {}
    if prompt_data.title is not None:
        update_data["title"] = prompt_data.title
    if prompt_data.content is not None:
        update_data["content"] = prompt_data.content
    
    if update_data:
        await db.execute(update(Prompt).where(Prompt.id == prompt_id).values(**update_data))
        await db.commit()
        await db.refresh(prompt)
    
    response = PromptResponse(
        id=prompt.id,
        user_id=prompt.user_id,
        title=prompt.title,
        content=prompt.content,
        state=prompt.state,
        view_count=prompt.view_count,
        like_count=prompt.like_count,
        favorite_count=prompt.favorite_count,
        created_at=prompt.created_at,
        updated_at=prompt.updated_at
    )
    
    return ResponseModel(data=response.model_dump(by_alias=True))

@router.delete("/{promptId}", response_model=ResponseModel)
async def delete_prompt(
    promptId: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    prompt_id = promptId
    result = await db.execute(
        select(Prompt).where(and_(Prompt.id == prompt_id, Prompt.user_id == current_user.id, Prompt.state == 1))
    )
    prompt = result.scalar_one_or_none()
    
    if not prompt:
        return ResponseModel(code=404, msg="提示词不存在或无权限")
    
    await db.execute(update(Prompt).where(Prompt.id == prompt_id).values(state=0))
    await db.commit()
    
    return ResponseModel(msg="删除成功")


@router.post("/{promptId}/like", response_model=ResponseModel)
async def like_prompt(
    promptId: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    prompt_id = promptId
    result = await db.execute(select(Prompt).where(and_(Prompt.id == prompt_id, Prompt.state == 1)))
    prompt = result.scalar_one_or_none()
    
    if not prompt:
        return ResponseModel(code=404, msg="提示词不存在")
    
    if prompt.user_id == current_user.id:
        return ResponseModel(code=400, msg="不能点赞自己的提示词")
    
    like_result = await db.execute(
        select(PromptLike).where(
            and_(PromptLike.prompt_id == prompt_id, PromptLike.user_id == current_user.id)
        )
    )
    existing_like = like_result.scalar_one_or_none()
    
    if existing_like:
        await db.delete(existing_like)
        await db.execute(
            update(Prompt).where(Prompt.id == prompt_id).values(like_count=Prompt.like_count - 1)
        )
        await db.commit()
        return ResponseModel(msg="取消点赞")
    else:
        new_like = PromptLike(prompt_id=prompt_id, user_id=current_user.id)
        db.add(new_like)
        await db.execute(
            update(Prompt).where(Prompt.id == prompt_id).values(like_count=Prompt.like_count + 1)
        )
        await db.commit()
        return ResponseModel(msg="点赞成功")

@router.post("/{promptId}/favorite", response_model=ResponseModel)
async def favorite_prompt(
    promptId: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    prompt_id = promptId
    result = await db.execute(select(Prompt).where(and_(Prompt.id == prompt_id, Prompt.state == 1)))
    prompt = result.scalar_one_or_none()
    
    if not prompt:
        return ResponseModel(code=404, msg="提示词不存在")
    
    if prompt.user_id == current_user.id:
        return ResponseModel(code=400, msg="不能收藏自己的提示词")
    
    fav_result = await db.execute(
        select(PromptFavorite).where(
            and_(PromptFavorite.prompt_id == prompt_id, PromptFavorite.user_id == current_user.id)
        )
    )
    existing_fav = fav_result.scalar_one_or_none()
    
    if existing_fav:
        await db.delete(existing_fav)
        await db.execute(
            update(Prompt).where(Prompt.id == prompt_id).values(favorite_count=Prompt.favorite_count - 1)
        )
        await db.commit()
        return ResponseModel(msg="取消收藏")
    else:
        new_fav = PromptFavorite(prompt_id=prompt_id, user_id=current_user.id)
        db.add(new_fav)
        await db.execute(
            update(Prompt).where(Prompt.id == prompt_id).values(favorite_count=Prompt.favorite_count + 1)
        )
        await db.commit()
        return ResponseModel(msg="收藏成功")

@router.get("/user/my-prompts", response_model=ResponseModel)
async def my_prompts(
    page: int = 1,
    pageSize: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    page_size = pageSize
    offset = (page - 1) * page_size
    
    query = select(Prompt).where(
        and_(Prompt.user_id == current_user.id, Prompt.state == 1)
    ).order_by(Prompt.created_at.desc())
    
    result = await db.execute(query.limit(page_size).offset(offset))
    prompts = result.scalars().all()
    
    count_result = await db.execute(
        select(func.count(Prompt.id)).where(
            and_(Prompt.user_id == current_user.id, Prompt.state == 1)
        )
    )
    total = count_result.scalar()
    
    prompt_list = [
        PromptResponse(
            id=p.id,
            user_id=p.user_id,
            title=p.title,
            content=p.content,
            state=p.state,
            view_count=p.view_count,
            like_count=p.like_count,
            favorite_count=p.favorite_count,
            created_at=p.created_at,
            updated_at=p.updated_at
        ) for p in prompts
    ]
    
    response = PromptListResponse(list=prompt_list, total=total, page=page, page_size=page_size)
    return ResponseModel(data=response.model_dump(by_alias=True))

@router.get("/user/favorites", response_model=ResponseModel)
async def my_favorites(
    page: int = 1,
    pageSize: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    page_size = pageSize
    offset = (page - 1) * page_size
    
    query = select(Prompt).join(PromptFavorite).where(
        and_(PromptFavorite.user_id == current_user.id, Prompt.state == 1)
    ).order_by(PromptFavorite.created_at.desc())
    
    result = await db.execute(query.limit(page_size).offset(offset))
    prompts = result.scalars().all()
    
    count_result = await db.execute(
        select(func.count(Prompt.id)).join(PromptFavorite).where(
            and_(PromptFavorite.user_id == current_user.id, Prompt.state == 1)
        )
    )
    total = count_result.scalar()
    
    prompt_list = [
        PromptResponse(
            id=p.id,
            user_id=p.user_id,
            title=p.title,
            content=p.content,
            state=p.state,
            view_count=p.view_count,
            like_count=p.like_count,
            favorite_count=p.favorite_count,
            created_at=p.created_at,
            updated_at=p.updated_at,
            is_favorited=True
        ) for p in prompts
    ]
    
    response = PromptListResponse(list=prompt_list, total=total, page=page, page_size=page_size)
    return ResponseModel(data=response.model_dump(by_alias=True))

@router.get("/user/likes", response_model=ResponseModel)
async def my_likes(
    page: int = 1,
    pageSize: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    page_size = pageSize
    offset = (page - 1) * page_size
    
    query = select(Prompt).join(PromptLike).where(
        and_(PromptLike.user_id == current_user.id, Prompt.state == 1)
    ).order_by(PromptLike.created_at.desc())
    
    result = await db.execute(query.limit(page_size).offset(offset))
    prompts = result.scalars().all()
    
    count_result = await db.execute(
        select(func.count(Prompt.id)).join(PromptLike).where(
            and_(PromptLike.user_id == current_user.id, Prompt.state == 1)
        )
    )
    total = count_result.scalar()
    
    prompt_list = [
        PromptResponse(
            id=p.id,
            user_id=p.user_id,
            title=p.title,
            content=p.content,
            state=p.state,
            view_count=p.view_count,
            like_count=p.like_count,
            favorite_count=p.favorite_count,
            created_at=p.created_at,
            updated_at=p.updated_at,
            is_liked=True
        ) for p in prompts
    ]
    
    response = PromptListResponse(list=prompt_list, total=total, page=page, page_size=page_size)
    return ResponseModel(data=response.model_dump(by_alias=True))

@router.get("/stats/global", response_model=ResponseModel)
async def get_stats(db: AsyncSession = Depends(get_db)):
    total_prompts_result = await db.execute(select(func.count(Prompt.id)).where(Prompt.state == 1))
    total_prompts = total_prompts_result.scalar()
    
    total_views_result = await db.execute(select(func.count(PromptView.id)))
    total_views = total_views_result.scalar()
    
    stats = StatsResponse(total_prompts=total_prompts, total_views=total_views)
    return ResponseModel(data=stats.model_dump(by_alias=True))
