from fastapi import FastAPI, Query, Body, HTTPException, Path
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional, Union, Literal
from math import ceil

app = FastAPI(title="Mini Blog")

BLOG_POST = [
    {"id": 1, "title": "Primero Post",
        "content": "Este es mi primer post en FastAPI."},
    {"id": 2, "title": "Segundo Post", "content": "Aprendiendo FastAPI es divertido!"},
    {"id": 3, "title": "Tercer Post",
     "content": "¡Estoy emocionado por construir más con FastAPI!"},
    {"id": 4, "title": "Cuarto Post", "content": "Explorando las rutas de FastAPI."},
    {"id": 5, "title": "Quinto Post", "content": "Manejo de datos con Pydantic."},
    {"id": 6, "title": "Sexto Post", "content": "Validación de modelos en FastAPI."},
    {"id": 7, "title": "Séptimo Post", "content": "Parámetros de consulta y ruta."},
    {"id": 8, "title": "Octavo Post", "content": "Manejo de errores HTTP."},
    {"id": 9, "title": "Noveno Post", "content": "Seguridad y autenticación."},
    {"id": 10, "title": "Décimo Post",
        "content": "Despliegue de aplicaciones FastAPI."},
    {"id": 11, "title": "Onceavo Post", "content": "Integración con bases de datos."},
    {"id": 12, "title": "Doceavo Post", "content": "Pruebas unitarias en FastAPI."},
    {"id": 13, "title": "Treceavo Post",
        "content": "Documentación automática con OpenAPI."},
    {"id": 14, "title": "Catorceavo Post", "content": "Middleware en FastAPI."},
    {"id": 15, "title": "Quinceavo Post", "content": "Dependencias e inyección."},
    {"id": 16, "title": "Dieciseisavo Post", "content": "WebSockets con FastAPI."},
    {"id": 17, "title": "Diecisieteavo Post",
        "content": "Tareas en segundo plano."},
    {"id": 18, "title": "Dieciochoavo Post", "content": "Generación de clientes."},
    {"id": 19, "title": "Diecinueveavo Post",
        "content": "Optimización de rendimiento."},
    {"id": 20, "title": "Veinteavo Post",
        "content": "Comunidad y recursos de FastAPI."}
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
    # [], crea una list apor cada objeto que se cree
    tags: Optional[List[Tag]] = Field(default_factory=list)
    author: Optional[Author] = None


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
    title: Optional[str] = Field(None, min_length=3, max_length=100)
    content: Optional[str] = Field(None, min_length=10, max_length=1000)


class PostPublic(PostBase):
    id: int


class PostSummary(BaseModel):
    id: int
    title: str


class PaginatedPost(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int
    has_prev: bool
    has_next: bool
    order_by: Literal["id", "title"]  # Siempre se proporciona
    direction: Literal["asc", "desc"]  # Siempre se proporciona
    search: Optional[str] = None  # Puede ser None si no se busca
    items: List[PostPublic]


# Root Endpoint
@app.get("/")
def home():
    return {"message": "Welcome to the Mini Blog!"}


# Query Parameter
# Define como quiero traer el recurso
@app.get("/posts", response_model=PaginatedPost)
def get_posts(query: Optional[str] = Query(
    default=None,
    title="Search Query",
    description="Query to search blog posts",
    alias="search",
    min_length=3,
    max_length=100,
    # Permite caracteres alfanumericos, espacios, signos de puntuacion y simbolos
    pattern="^[\w\s\p{P}\p{S}]+$",
),
    per_page: int = Query(
        default=10,
        title="Posts per page",
        description="Number of posts to retrieve",
        ge=1,
        le=50,
),
    page: int = Query(
        default=1,
        title="Page",
        description="Page number to retrieve",
        ge=1,
),
    order_by: Literal["id", "title"] = Query(
        default="id",
        title="Order By",
        description="Field to order the posts by"
),
    direction: Literal["asc", "desc"] = Query(
        default="asc",
        title="Direction",
        description="Direction to order the posts by"
),
):
    # ========== PASO 1: FILTRADO DE RESULTADOS ==========
    # Inicializar con todos los posts disponibles
    results = BLOG_POST

    # Si se proporciona un parámetro de búsqueda (query), filtrar los posts
    # que contengan el término de búsqueda en el título (case-insensitive)
    if query:
        results = [post for post in BLOG_POST if query.lower()
                   in post["title"].lower()]

    # ========== PASO 2: CALCULAR TOTAL Y PÁGINAS ==========
    # Contar el total de resultados después del filtrado
    total = len(results)

    # Calcular el total de páginas necesarias usando ceil (redondeo hacia arriba)
    # Ejemplos:
    #   - total=29, per_page=10 → ceil(29/10) = ceil(2.9) = 3 páginas
    #   - total=30, per_page=10 → ceil(30/10) = ceil(3.0) = 3 páginas
    #   - total=0, per_page=10 → 0 páginas (caso especial)
    total_pages = ceil(total / per_page) if total > 0 else 0

    # ========== PASO 3: VALIDAR PÁGINA ACTUAL ==========
    # Si no hay resultados, establecer página actual en 1 (por defecto)
    if total_pages == 0:
        current_page = 1
    else:
        # Asegurar que la página solicitada no exceda el total de páginas
        # Si el usuario pide página 10 pero solo hay 3, devolver página 3
        # Ejemplo: page=10, total_pages=3 → min(10, 3) = 3
        current_page = min(page, total_pages)

    # ========== PASO 4: ORDENAMIENTO ==========
    # Ordenar los resultados según el campo especificado (order_by: "id" o "title")
    # - key=lambda: define qué campo usar para ordenar
    # - reverse=True si direction=="desc" (descendente: Z-A, 10-1)
    # - reverse=False si direction=="asc" (ascendente: A-Z, 1-10)
    results = sorted(
        results, key=lambda post: post[order_by], reverse=direction == "desc")

    # ========== PASO 5: EXTRACCIÓN DE ITEMS DE LA PÁGINA ACTUAL ==========
    # Si no hay páginas (total_pages=0), devolver lista vacía
    if total_pages == 0:
        items = []
    else:
        # Calcular el índice de inicio para la página actual
        # Página 1: (1-1) * 10 = 0 → empieza en índice 0
        # Página 2: (2-1) * 10 = 10 → empieza en índice 10
        # Página 3: (3-1) * 10 = 20 → empieza en índice 20
        start = (current_page - 1) * per_page

        # Extraer los items usando slicing
        # Ejemplos:
        #   - Página 1, per_page=10 → results[0:10] (items 0-9)
        #   - Página 2, per_page=10 → results[10:20] (items 10-19)
        #   - Página 3, per_page=10 → results[20:30] (items 20-29)
        items = results[start: start + per_page]

    # ========== PASO 6: BANDERAS DE NAVEGACIÓN ==========
    # ¿Existe una página anterior?
    # True si current_page > 1 (no estamos en la primera página)
    has_prev = current_page > 1

    # ¿Existe una página siguiente?
    # True si current_page < total_pages (no estamos en la última página)
    # Ejemplo: current_page=2, total_pages=3 → 2 < 3 → True
    has_next = current_page < total_pages

    # ========== PASO 7: RETORNAR RESPUESTA PAGINADA ==========
    # Crear y retornar el objeto PaginatedPost con toda la metadata de paginación
    return PaginatedPost(
        page=current_page,      # Número de página actual (validada)
        per_page=per_page,      # Cantidad de items por página
        # Total de items encontrados (después del filtrado)
        total=total,
        total_pages=total_pages,  # Total de páginas disponibles
        has_prev=has_prev,      # Booleano: ¿hay página anterior?
        has_next=has_next,      # Booleano: ¿hay página siguiente?
        order_by=order_by,      # Campo usado para ordenar ("id" o "title")
        direction=direction,    # Dirección del ordenamiento ("asc" o "desc")
        search=query,           # Término de búsqueda aplicado (si existe)
        items=items             # Lista de posts de la página actual
    )


# Path Parameter
# Define como quiero traer un recurso especifico
@app.get("/posts/{post_id}", response_model=Union[PostPublic, PostSummary], response_description="Blog post detail")
def get_post(post_id: int = Path(
    ...,
    ge=1,
    title="Post ID",
    description="ID of the post to retrieve. Should be a positive integer.",
), include_content: bool = Query(default=True, description="Incluir el contenido del post")):
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
