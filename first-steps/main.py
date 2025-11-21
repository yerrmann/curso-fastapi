from fastapi import FastAPI, Query, Body, HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional, Union

app = FastAPI(title="Mini Blog")

BLOG_POST = [
    {"id": 1, "title": "Hola desde FastAPI",
        "content": "Este es mi primer post en FastAPI."},
    {"id": 2, "title": "Segundo Post", "content": "Aprendiendo FastAPI es divertido!"},
    {"id": 3, "title": "Tercer Post",
     "content": "¡Estoy emocionado por construir más con FastAPI!"}
]

PROHIBITED_WORDS = [
    "spam", "tonto", "idiota", "basura", "malo",
    "estúpido", "inútil", "feo", "horrible"
]


class Tag(BaseModel):
    name: str = Field(..., min_length=2, max_length=30,
                      description="Name of the tag")


class Author(BaseModel):
    name: str = Field(..., min_length=2, max_length=50,
                      description="Name of the author")
    email: Optional[EmailStr] = Field(None, description="Email of the author")


class PostBase(BaseModel):
    title: str
    content: Optional[str] = "Content not available"
    tags: Optional[List[Tag]] = []
    author: Optional[Author] = None
    email: Optional[EmailStr] = None


class PostCreate(BaseModel):
    title: str = Field(...,
                       title="Title of the post",
                       min_length=3,
                       max_length=100,
                       description="The title must be between 3 and 100 characters",
                       examples=["My First Post", "Learning FastAPI",
                                 "Building APIs with Python"]
                       )
    content: Optional[str] = Field(None,
                                   title="Content of the post",
                                   min_length=10,
                                   max_length=1000,
                                   description="The content of the blog post",
                                   examples=["This is the content of my first post.",
                                             "FastAPI makes it easy to build APIs."]
                                   )

    tags: Optional[List[Tag]] = []

    @field_validator("title")
    @classmethod
    def not_allowed_title(cls, value: str) -> str:
        if any(prohibited_word in value.lower() for prohibited_word in PROHIBITED_WORDS):
            raise ValueError(
                f"The title cannot contain prohibited words: {', '.join(PROHIBITED_WORDS)}")
        return value


class PostUpdate(BaseModel):
    title: str
    content: Optional[str] = None


class PostPublic(PostBase):
    id: int


class PostSummary(BaseModel):
    id: int
    title: str

# Root Endpoint


@app.get("/")
def home():
    return {"message": "Welcome to the Mini Blog!"}


# Query Parameter
# Define como quiero traer el recurso
@app.get("/posts", response_model=List[PostPublic])
def get_posts(query: str | None = Query(default=None, title="Search Query", description="Query to search blog posts")):
    if query:
        return [post for post in BLOG_POST if query.lower()
                in post["title"].lower()]
    return BLOG_POST


# Path Parameter
# Define como quiero traer un recurso especifico
@app.get("/posts/{post_id}", response_model=Union[PostPublic, PostSummary], response_description="Blog post detail")
def get_post(post_id: int, include_content: bool = Query(default=True, description="Incluir el contenido del post")):
    for post in BLOG_POST:
        if post["id"] == post_id:
            if not include_content:
                return PostSummary(id=post["id"], title=post["title"])
            return post
    raise HTTPException(status_code=404, detail="Post not found")


# Query parameter para filtrar si queremos incluir el contenido o no
@app.get("/posts/{post_id}/detail")
def get_post_detail(post_id: int, include_content: bool = Query(default=False, description="Incluir o no el contenido")):
    for post in BLOG_POST:
        if post["id"] == post_id:
            if include_content:
                return {"post": post}
            return {"post": {"id": post["id"], "title": post["title"]}}
    raise HTTPException(status_code=404, detail="Post not found")


# POST
# "..." elipsis, indica que es un campo obligatorio
@app.post("/posts", response_model=PostPublic, response_description="Post created successfully", status_code=201)
def create_post(post: PostCreate):
    new_id = (BLOG_POST[-1]["id"] + 1) if BLOG_POST else 1
    new_post = {"id": new_id,
                "title": post.title,
                "content": post.content,
                # List comprehension to convert Tag models to dicts
                "tags": [tag.model_dump() for tag in post.tags],
                "author": post.author.model_dump() if post.author else None,
                }

    BLOG_POST.append(new_post)
    return new_post

# PUT


@app.put("/posts/{post_id}", response_model=PostPublic, response_description="Post updated successfully", response_model_exclude_none=True, status_code=200)
def update_post(post_id: int, updated_post: PostUpdate):
    if post_id == "":
        return {"error": "Post ID is required"}
    for post in BLOG_POST:
        if post["id"] == post_id:
            playload = updated_post.model_dump(exclude_unset=True)
            if "title" in playload:
                post["title"] = playload["title"]
            if "content" in playload:
                post["content"] = playload["content"]
            return post
    raise HTTPException(status_code=404, detail="Post not found")


# DELETE
@app.delete("/posts/{post_id}", status_code=204)
def delete_post(post_id: int):
    for index, post in enumerate(BLOG_POST):
        if post["id"] == post_id:
            del BLOG_POST[index]
            return
    raise HTTPException(status_code=404, detail="Post not found")
