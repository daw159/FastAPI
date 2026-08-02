from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

users = [
    {
        "id": 1,
        "name": "Ali",
        "age": 20,
        "email": "ali@example.com",
        "is_active": True
    },
    {
        "id": 2,
        "name": "Sara",
        "age": 22,
        "email": "sara@example.com",
        "is_active": True
    },
    {
        "id": 3,
        "name": "Ahmed",
        "age": 19,
        "email": "ahmed@example.com",
        "is_active": False
    },
    {
        "id": 4,
        "name": "Fatima",
        "age": 24,
        "email": "fatima@example.com",
        "is_active": True
    },
    {
        "id": 5,
        "name": "Usman",
        "age": 21,
        "email": "usman@example.com",
        "is_active": False
    }
]

@app.get("/", response_class=HTMLResponse,include_in_schema=False)
@app.get("/posts", response_class=HTMLResponse,include_in_schema=False)
def root():
    return f"<h1>{users[0]['name']}</h1>"


@app.get("/api/posts")
def gets_posts():
    return users
