from fastapi import FastAPI, Request,HTTPException,status,Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as starletteexception
from schemas import PostCreate ,PostResponse,UserCreate,UserResponse
from sqlalchemy import select
from sqlalchemy.orm import Session as session
from database import Base,engine,get_db
import model
from typing import Annotated

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory="templates")

# posts: list[dict] = [
#     {
#         "id": 1,
#         "author": "Mian David",
#         "title": "FastAPI is Awesome",
#         "content": "This framework is really easy to use and super fast.",
#         "date_posted": "April 20, 2025",
#     },
#     {
#         "id": 2,
#         "author": "Joonny Deol",
#         "title": "Python is Great for Web Development",
#         "content": "Python is a great language for web development, and FastAPI makes it even better.",
#         "date_posted": "April 21, 2025",
#     },
# ]


@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
def home(request: Request,db:Annotated[session,Depends(get_db)]):
    
    result=db.execute(select(model.Post))
    posts=result.scalars().all()
    return templates.TemplateResponse(
        request,
        "home.html",
        {"posts": posts, "title": "Home"},
    )


@app.get("/posts/{post_id}")
def post_page(post_id: int,request: Request,db:Annotated[session,Depends(get_db)]):
    
    result = db.execute(select(model.Post).where(model.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id {post_id} not found")
    title = post.title[:50]
    return templates.TemplateResponse(request, "post.html", {"post": post, "title": title})
    
    


@app.post("/api/users",response_model=UserResponse,status_code=status.HTTP_201_CREATED)
def create_user(user:UserCreate,db:Annotated[session,Depends(get_db)]):
    result=db.execute(
        select(model.User).where(model.User.username==user.username),
    )
    existing_user=result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exits",
        )
        
    result=db.execute(
            select(model.User).where(model.User.email==user.email),
        )
    
    existing_email=result.scalars().first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exits",
        )
        
    new_user=model.User(
            username=user.username,
            email=user.email,
        )
        
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
        
        
@app.get("/api/users/{user_id}",response_model=UserResponse)  
def get_user(user_id:int,db:Annotated[session,Depends(get_db)]):
      result=db.execute(
              select(model.User).where(model.User.id==user_id),
          )
      user=result.scalars().first()
      if user:
          return user
      
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User NOT Found ")
  
  
@app.get("/api/users/{user_id}/posts",response_model=list[PostResponse])

def get_user_posts(user_id: int, db: Annotated[session, Depends(get_db)]):
    result = db.execute(select(model.User).where(model.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found")

    result = db.execute(select(model.Post).where(model.Post.user_id == user_id))
    posts = result.scalars().all()
    return posts

@app.get("/users/{user_id}/posts", include_in_schema=False, name="user_posts")
def get_user_post_page(
    request: Request,
    user_id: int,
    db: Annotated[session, Depends(get_db)],
):
    result = db.execute(select(model.User).where(model.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user Not Found")

    result = db.execute(select(model.Post).where(model.Post.user_id == user_id))
    posts = result.scalars().all()

    return templates.TemplateResponse(
        request,
        "user_posts.html",
        {"posts": posts, "user": user, "title": f"{user.username}'s Posts"},
    )   

@app.get("/api/posts",response_model=list[PostResponse])
def get_posts(db: Annotated[session, Depends(get_db)]):
    result=db.execute(select(model.Post))
    posts=result.scalars().all()
    return posts


@app.post("/api/posts",response_model=PostResponse,status_code=status.HTTP_201_CREATED)
def create_post(post:PostCreate,db: Annotated[session, Depends(get_db)]):
    result=db.execute(select(model.User).where(model.User.id==post.user_id))
    user=result.scalars().first()
    
    if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="user Not Found",
                
            )
            
    new_post=model.Post(
        title=post.title,
        content=post.content,
        user_id=post.user_id,     
    )
    
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    return new_post



@app.get("/api/posts/{post_id}",response_model=PostResponse)
def get_post(post_id: int,db: Annotated[session, Depends(get_db)]):
    result = db.execute(select(model.Post).where(model.Post.id == post_id))
    post = result.scalars().first()
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post not found")


@app.exception_handler(starletteexception)
def general_http_exception(request:Request,exception:starletteexception):
    messege=(
        exception.detail
        if exception.detail
        else f"An error occured please check your request and try again"
    )
    
    if request.url.path.startswith('/api'):
        return JSONResponse(
            status_code=exception.status_code,
            content={"detail":messege},
        )
        
    return templates.TemplateResponse(
        request,
        "error.html",
        {
        "status_code": exception.status_code,
        "title": exception.status_code,
        "messege": messege,
        },
        
        status_code=exception.status_code,
    )
        
        
@app.exception_handler(RequestValidationError)
def validation_exceptionhandler(request:Request,exception:RequestValidationError):
    if request.url.path.startswith('/api'):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail":exception.errors()},
        )
        
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code":status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title":status.HTTP_422_UNPROCESSABLE_CONTENT,
            "messege":"Invalid request please check your internet and try again"
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
