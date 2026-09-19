from fastapi import HTTPException,status,Depends,Query
from sqlalchemy.orm  import selectinload
from database import get_db
from schemas import PostCreate ,PostResponse,UserCreate,PostUpdate,UserUpdate,PaginatedPostsResponse
from sqlalchemy import select,func
from sqlalchemy.ext.asyncio import AsyncSession
import model
from typing import Annotated
from fastapi import APIRouter
from auth import CurrentUser


router=APIRouter()


@router.get("", response_model=PaginatedPostsResponse)
async def get_posts(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
):

    count_result = await db.execute(select(func.count()).select_from(model.Post))
    total = count_result.scalar() or 0

    result = await db.execute(
        select(model.Post)
        .options(selectinload(model.Post.author))
        .order_by(model.Post.date_posted.desc())
        .offset(skip)
        .limit(limit),
    )
    posts = result.scalars().all()

    has_more = skip + len(posts) < total

    return PaginatedPostsResponse(
        posts=[PostResponse.model_validate(post) for post in posts],
        total=total,
        skip=skip,
        limit=limit,
        has_more=has_more,
    )


@router.post("",response_model=PostResponse,status_code=status.HTTP_201_CREATED)
async def create_post(post:PostCreate,current_user:CurrentUser,db: Annotated[AsyncSession, Depends(get_db)]):
    
            
    new_post=model.Post(
        title=post.title,
        content=post.content,
        user_id=current_user.id,
            
    )
    
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post,attribute_names=["author"])
    
    return new_post



@router.get("/{post_id}",response_model=PostResponse)
async def get_post(post_id: int,db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(model.Post).options(selectinload(model.Post.author)).where(model.Post.id == post_id))
    post = result.scalars().first()
    if not post:        
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post not found")
    return post
    

@router.put("/{post_id}", response_model=PostResponse)
async def update_post_full(post_id: int, post_data: PostCreate,current_user:CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(model.Post).where(model.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post not found")

    if post.user_id!=current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to update this post")

    post.title = post_data.title
    post.content = post_data.content   # you were missing this — content never got updated either

    await db.commit()
    await db.refresh(post,attribute_names=["author"])
    return post


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post_partial(post_id: int,current_user:CurrentUser, post_data: PostUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(model.Post).where(model.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post not found")
    
    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this post",
        )

    update_data= post_data.model_dump(exclude_unset=True)
    
    
    for field, value in update_data.items():
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post,attribute_names=["author"])
    return post

@router.delete("/{post_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int,current_user:CurrentUser,db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(model.Post).where(model.Post.id == post_id))
    post = result.scalars().first()
    if not post:        
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post not found")
    
    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this post",
        )
    
    await db.delete(post)
    await db.commit()