from sqlmodel import Field, SQLModel
from pydantic import EmailStr

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

class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)