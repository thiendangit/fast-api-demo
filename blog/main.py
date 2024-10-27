from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Response, status

from blog import schemas
from typing import Annotated, Dict, Any

from db import create_db_and_tables, SessionDep

@asynccontextmanager
async def lifespan(_):
    create_db_and_tables()
    yield
app = FastAPI(lifespan=lifespan)

@app.get("/blogs", status_code=200)
def get_blogs_list(session: SessionDep, offset: int = 0,
              limit: Annotated[int, Query(le=10)] = 10) -> list[schemas.Blog]:
    return session.query(schemas.Blog).limit(limit).offset(offset).all()

@app.get("/blog/{id}", status_code=200)
def get_blog_by_id(id: str, response: Response, session: SessionDep) -> dict[str, str] | Any:
    blog = session.query(schemas.Blog).filter(schemas.Blog.id == id).first()
    if not blog:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'detail': f'Blog with id = {id} does not exist'}
    return  blog

@app.post("/blog", status_code=200)
def create_blog(blog: schemas.BlogBase, session: SessionDep) -> schemas.Blog:
    db_blog = schemas.Blog.model_validate(blog)
    session.add(db_blog)
    session.commit()
    session.refresh(db_blog)
    return db_blog

@app.delete("/blog/{id}", status_code=200)
def delete_blog(id: str, response: Response, session: SessionDep) -> dict[str, str] | Any:
    blog = session.get(schemas.Blog, id)
    if not blog:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'detail': f'Blog with id = {id} does not exist'}
    session.delete(blog)
    session.commit()
    return {"ok": True}

@app.patch("/blog/{id}", status_code=200)
def update_blog(id: str, blogParam: schemas.BlogBase, response: Response, session: SessionDep) -> dict[str, str] | Any:
    blog = session.get(schemas.Blog, id)
    if not blog:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'detail': f'Blog with id = {id} does not exist'}
    blog_data = blogParam.model_dump(exclude_unset=True)
    blog.sqlmodel_update(blog_data)
    session.add(blog)
    session.commit()
    session.refresh(blog)
    return blog