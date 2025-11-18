from fastapi import FastAPI, Query, Body, HTTPException

app = FastAPI(title="Mini Blog")

BLOG_POST = [
    {"id": 1, "title": "Hola desde FastAPI",
        "content": "Este es mi primer post en FastAPI."},
    {"id": 2, "title": "Segundo Post", "content": "Aprendiendo FastAPI es divertido!"},
    {"id": 3, "title": "Tercer Post",
     "content": "¡Estoy emocionado por construir más con FastAPI!"}
]


@app.get("/")
def home():
    return {"message": "Welcome to the Mini Blog!"}


# Query Parameter
# Define como quiero traer el recurso
@app.get("/posts")
def get_posts(query: str | None = Query(default=None, title="Search Query", description="Query to search blog posts")):
    if query:
        results = [post for post in BLOG_POST if query.lower()
                   in post["title"].lower()]
        return {"posts": results, "query": query}
    return {"posts": BLOG_POST}


# Path Parameter
# Define como quiero traer un recurso especifico
@app.get("/posts/{post_id}")
def get_post(post_id: int):
    for post in BLOG_POST:
        if post["id"] == post_id:
            return {"post": post}
    return {"error": "Post not found"}


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
@app.post("/posts")
def create_post(post: dict = Body(...)):
    if "title" not in post or "content" not in post:
        return {"error": "Title and content are required"}
    if "title" == "" or "content" == "":
        return {"error": "Title and content cannot be empty"}
    new_id = (BLOG_POST[-1]["id"] + 1) if BLOG_POST else 1
    new_post = {"id": new_id,
                "title": post["title"], "content": post["content"]}

    BLOG_POST.append(new_post)
    return {"message": "Post created successfully", "post": new_post}


# PUT
@app.put("/posts/{post_id}")
def update_post(post_id: int, updated_post: dict = Body(...)):
    if post_id == "":
        return {"error": "Post ID is required"}
    for post in BLOG_POST:
        if post["id"] == post_id:
            post["title"] = updated_post.get("title", post["title"])
            post["content"] = updated_post.get("content", post["content"])
            raise HTTPException(
                status_code=200, detail="Post updated successfully", headers={"post": str(post)})
    raise HTTPException(status_code=404, detail="Post not found")


# DELETE
@app.delete("/posts/{post_id}", status_code=204)
def delete_post(post_id: int):
    for index, post in enumerate(BLOG_POST):
        if post["id"] == post_id:
            del BLOG_POST[index]
            return
    raise HTTPException(status_code=404, detail="Post not found")
