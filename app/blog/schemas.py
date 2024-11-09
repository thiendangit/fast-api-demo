from sqlmodel import Field, SQLModel
from pydantic import EmailStr
from pydantic import BaseModel

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class BlogBase(SQLModel):
    title: str = Field()
    body: str

class Blog(BlogBase, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)

class ShowBlg(BlogBase):
    class Config:
        orm_mode = True


class UserBase(SQLModel):
    name: str
    email: EmailStr
    password: str

class ShowUserBase(SQLModel):
    name: str
    email: EmailStr


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)

class ShowUser(ShowUserBase):
    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None

class UserInDB(User):
    hashed_password: str