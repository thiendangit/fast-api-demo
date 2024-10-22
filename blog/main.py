from contextlib import asynccontextmanager
from fastapi import FastAPI, Query

from blog import schemas
from typing import Annotated


from db import create_db_and_tables, SessionDep

@asynccontextmanager
async def lifespan(_):
    create_db_and_tables()
    yield
app = FastAPI(lifespan=lifespan)

@app.get("/blogs")
def get_blogs_list(session: SessionDep, offset: int = 0,
              limit: Annotated[int, Query(le=10)] = 10) -> list[schemas.Blog]:
    return session.query(schemas.Blog).limit(limit).offset(offset).all()

@app.post("/blog")
def create_blog(blog: schemas.BlogBase, session: SessionDep) -> schemas.Blog:
    db_blog = schemas.Blog.model_validate(blog)
    session.add(db_blog)
    session.commit()
    session.refresh(db_blog)
    return db_blog