from contextlib import asynccontextmanager
from typing import Annotated, Any
from datetime import datetime, timedelta

from fastapi import FastAPI, Query, Response, status, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from jwt.exceptions import InvalidTokenError

from blog import schemas
from blog.hash import Hash
from db import create_db_and_tables, SessionDep

@asynccontextmanager
async def lifespan(_):
    create_db_and_tables()
    yield

app = FastAPI(
    lifespan=lifespan,
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
        "clientId": "blog-client"
    }
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login",
    scopes={},
    description="JWT token from login"
)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, schemas.SECRET_KEY, algorithm=schemas.ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: SessionDep
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, schemas.SECRET_KEY, algorithms=[schemas.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    
    user = session.query(schemas.User).filter(schemas.User.email == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

@app.post("/login", response_model=schemas.Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep
):
    user = session.query(schemas.User).filter(schemas.User.email == form_data.username).first()
    if not user or not Hash.verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=schemas.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/blogs", status_code=200, response_model=list[schemas.ShowBlg], tags=["blog"])
def get_blogs_list(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=10)] = 10
):
    return session.query(schemas.Blog).limit(limit).offset(offset).all()

@app.get("/blog/{id}", status_code=200, tags=["blog"])
def get_blog_by_id(id: str, response: Response, session: SessionDep) -> dict[str, str] | Any:
    blog = session.query(schemas.Blog).filter(schemas.Blog.id == id).first()
    if not blog:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'detail': f'Blog with id = {id} does not exist'}
    return blog

@app.post("/blog", status_code=200, response_model=schemas.Blog, tags=["blog"])
def create_blog(
    blog: schemas.BlogBase,
    session: SessionDep,
    current_user: Annotated[schemas.User, Depends(get_current_user)]
) -> schemas.Blog:
    db_blog = schemas.Blog.model_validate(blog)
    db_blog.author_id = current_user.id
    session.add(db_blog)
    session.commit()
    session.refresh(db_blog)
    return db_blog

@app.delete("/blog/{id}", status_code=200, tags=["blog"])
def delete_blog(
    id: str,
    response: Response,
    session: SessionDep,
    current_user: Annotated[schemas.User, Depends(get_current_user)]
) -> dict[str, str] | Any:
    blog = session.get(schemas.Blog, id)
    if not blog:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'detail': f'Blog with id = {id} does not exist'}
    if blog.author_id != current_user.id:
        response.status_code = status.HTTP_403_FORBIDDEN
        return {'detail': 'Not authorized to delete this blog'}
    session.delete(blog)
    session.commit()
    return {"ok": True}

@app.patch("/blog/{id}", status_code=200, tags=["blog"])
def update_blog(
    id: str,
    blog_param: schemas.BlogBase,
    response: Response,
    session: SessionDep,
    current_user: Annotated[schemas.User, Depends(get_current_user)]
) -> dict[str, str] | Any:
    blog = session.get(schemas.Blog, id)
    if not blog:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'detail': f'Blog with id = {id} does not exist'}
    if blog.author_id != current_user.id:
        response.status_code = status.HTTP_403_FORBIDDEN
        return {'detail': 'Not authorized to update this blog'}
    blog_data = blog_param.model_dump(exclude_unset=True)
    for key, value in blog_data.items():
        setattr(blog, key, value)
    session.add(blog)
    session.commit()
    session.refresh(blog)
    return blog

@app.post('/user', status_code=200, tags=["user"])
def create_user(
    user: schemas.UserBase,
    session: SessionDep,
    response: Response
) -> schemas.User | dict[str, str]:
    existing_user = session.query(schemas.User).filter(schemas.User.email == user.email).first()
    if existing_user:
        response.status_code = status.HTTP_409_CONFLICT
        return {'detail': f"Email {user.email} is already existed"}

    user.password = Hash.get_password_hash(user.password)
    db_user = schemas.User.model_validate(user)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@app.get('/user/{id}', status_code=200, response_model=schemas.ShowUser, tags=["user"])
def get_user_by_id(id: str, response: Response, session: SessionDep) -> dict[str, str] | Any:
    user = session.query(schemas.User).filter(schemas.User.id == id).first()
    if not user:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'detail': f'User with id = {id} does not exist'}
    return user