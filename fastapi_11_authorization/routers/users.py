from fastapi import FastAPI, Request,HTTPException,status,Depends
from sqlalchemy.orm  import selectinload
from database import get_db
from schemas import PostCreate ,PostResponse,UserCreate,PostUpdate,UserUpdate,UserPublic,UserPrivate,Token
from sqlalchemy import select,func
from sqlalchemy.ext.asyncio import AsyncSession
import model
from typing import Annotated
from fastapi import APIRouter
from auth import verify_password,hash_password,create_access_token,CurrentUser
from config import settings
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm

router=APIRouter()

@router.post("",response_model=UserPrivate,status_code=status.HTTP_201_CREATED)
async def create_user(user:UserCreate,db:Annotated[AsyncSession,Depends(get_db)]):
    result=await db.execute(
        select(model.User).where(func.lower(model.User.username)==user.username.lower()),
    )
    existing_user=result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exits",
        )
        
    result=await db.execute(
            select(model.User).where(func.lower(model.User.email)==user.email.lower()),
        )
    
    existing_email=result.scalars().first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exits",
        )
        
    new_user=model.User(
            username=user.username,
            email=user.email.lower(),
            password_hash=hash_password(user.password)
        )
        
    db.add(new_user)
    await  db.commit()
    await  db.refresh(new_user)
    return new_user
 
@router.get("/me", response_model=UserPrivate)
async def get_current_user(current_user:CurrentUser):
    return current_user
     
      
@router.get("/{user_id}",response_model=UserPublic)  
async def get_user(user_id:int,db:Annotated[AsyncSession,Depends(get_db)]):
      result=await db.execute(
              select(model.User).where(model.User.id==user_id),
          )
      user=result.scalars().first()
      if user:
          return user
      
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User NOT Found ")
  
@router.get("/{user_id}/posts", name="user_posts", response_model=list[PostResponse])
async def get_user_posts(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(model.User).where(model.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found")

    result = await db.execute(
        select(model.Post)
        .options(selectinload(model.Post.author))
        .where(model.Post.user_id == user_id)
        .order_by(model.Post.date_posted.desc())
    )
    posts = result.scalars().all()
    return posts

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    
    # Look up user by email (case-insensitive)
    # Note: OAuth2PasswordRequestForm uses "username" field, but we treat it as email
    result = await db.execute(
        select(model.User).where(
            func.lower(model.User.email) == form_data.username.lower(),
        ),
    )
    user = result.scalars().first()
    
    if not user or not verify_password(form_data.password,user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Inorrect username or password",headers={"WWW-Authenticate": "Bearer"})
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires,
    )
    return Token(access_token=access_token, token_type="bearer")  




@router.patch("/{user_id}", response_model=UserPrivate)
async def update_user(
    user_id: int,user_update: UserUpdate,current_user:CurrentUser,db: Annotated[AsyncSession, Depends(get_db)],
):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user",
        )
    
    result = await db.execute(select(model.User).where(model.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
        
    if user_update.username is not None and user_update.username.lower() !=user.username.lower():
        result = await db.execute(
            select(model.User).where(model.User.username == user_update.username),
        )
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_NOT_FOUND,detail="User already exits")

    if user_update.email is not None and user_update.email != user.email:
        result = await db.execute(
            select(model.User).where(model.User.email == user_update.email),
        )
        existing_email = result.scalars().first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
    if user_update.username is not None:
        user.username = user_update.username
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.image_file is not None:
        user.image_file = user_update.image_file

    await db.commit()
    await db.refresh(user)
    return user
        
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int,current_user:CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    
    result = await db.execute(select(model.User).where(model.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await db.delete(user)
    await db.commit()     
