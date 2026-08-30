from fastapi import FastAPI, Request,HTTPException,status,Depends,APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm  import selectinload
from starlette.exceptions import HTTPException as starletteexception
from schemas import PostCreate ,PostResponse,UserCreate,UserPrivate,PostUpdate,UserUpdate,UserPublic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import Base,engine,get_db
import model
from typing import Annotated
from contextlib import asynccontextmanager
from fastapi.exception_handlers import request_validation_exception_handler,http_exception_handler
from routers import users,posts



@asynccontextmanager
async  def lifespan(_app:FastAPI):
    async with engine.begin() as conn:
         await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(lifespan=lifespan)   # ← currently missing this argument

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(users.router,prefix="/api/users",tags=["users"])
app.include_router(posts.router,prefix="/api/posts",tags=["posts"])

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
async def home(request: Request,db:Annotated[AsyncSession,Depends(get_db)]):
    
    result = await db.execute(
    select(model.Post)
    .options(selectinload(model.Post.author))
    .order_by(model.Post.date_posted.desc())
)

    posts=result.scalars().all()
    return templates.TemplateResponse(
        request,
        "home.html",
        {"posts": posts, "title": "Home"},
    )


@app.get("/login", include_in_schema=False)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "login.html",
        {"title": "Login"},
    )


@app.get("/register", include_in_schema=False)
async def register_page(request: Request):
    return templates.TemplateResponse(
        request,
        "register.html",
        {"title": "Register"},
    )


@app.get("/posts/{post_id}")
async def post_page(post_id: int, request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(model.Post).options(selectinload(model.Post.author)).where(model.Post.id == post_id)
    )
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id {post_id} not found")
    title = post.title[:50]
    return templates.TemplateResponse(request, "post.html", {"post": post, "title": title})
    

@app.get("/users/{user_id}/posts", include_in_schema=False, name="user_posts")
async def get_user_post_page(
    request: Request,
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(model.User).where(model.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user Not Found")

    result = await db.execute(select(model.Post).options(selectinload(model.Post.author)).where(model.Post.user_id == user_id))
    posts = result.scalars().all()

    return templates.TemplateResponse(
        request,
        "user_posts.html",
        {"posts": posts, "user": user, "title": f"{user.username}'s Posts"},
    )   


@app.exception_handler(starletteexception)
async def general_http_exception(request:Request,exception:starletteexception):
    
    if request.url.path.startswith('/api'):
        return await http_exception_handler(request,exception)
    messege=(
        exception.detail
        if exception.detail
        else f"An error occured please check your request and try again"
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
async def validation_exceptionhandler(request:Request,exception:RequestValidationError):
    if request.url.path.startswith('/api'):
        return await request_validation_exception_handler(request,exception)
        
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
