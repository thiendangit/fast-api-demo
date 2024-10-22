from sqlmodel import Field, SQLModel

class BlogBase(SQLModel):
    title: str = Field()
    body: str

class Blog(BlogBase, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)