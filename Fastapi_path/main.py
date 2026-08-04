from fastapi import FastAPI, Request,HTTPException,status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as starletteexception

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

posts: list[dict] = [
    {
        "id": 1,
        "author": "Mian David",
        "title": "FastAPI is Awesome",
        "content": "This framework is really easy to use and super fast.",
        "date_posted": "April 20, 2025",
    },
    {
        "id": 2,
        "author": "Joonny Deol",
        "title": "Python is Great for Web Development",
        "content": "Python is a great language for web development, and FastAPI makes it even better.",
        "date_posted": "April 21, 2025",
    },
]


@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
def home(request: Request):
    return templates.TemplateResponse(
        request,
        "home.html",
        {"posts": posts, "title": "Home"},
    )


@app.get("/posts/{post_id}")
def post_page(post_id: int,request: Request):
    for post in posts:
        if post["id"] == post_id:
            title=post['title'][:50]
            return templates.TemplateResponse(
                    request,
                    "post.html",
                    {"post": post, "title": title},
                )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,detail=f"Post with id {post_id} not found")


@app.get("/api/posts")
def get_posts():
    return posts


@app.get("/api/posts/{post_id}")
def get_post(post_id: int):
    for post in posts:
        if post["id"] == post_id:
            return post
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,detail=f"Post with id {post_id} not found")


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
