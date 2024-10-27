from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

class Blog(BaseModel):
    timestamp: str
    dimensions: tuple[int, int]

@app.post("/blog")
async def create_blog(blog: Blog):
    return {"message": f"Hello {blog.timestamp}"}