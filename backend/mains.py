import os
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from auth import routes
from database import Base, engine
from embedding_utils import _load_model
from routes import (
    achievements,
    ai_chat,
    certificates,
    document_embeddings,
    education,
    internship,
    projects,
    resume,
    skills,
    user_details,
)

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the embedding model in the background so the first chat/resume request doesn't pay the ~4s load.
    threading.Thread(target=_load_model, daemon=True).start()
    yield


dapp = FastAPI(
    lifespan=lifespan,
    title="Make My Resume API",
    version="1.0.0",
    description="Backend API for a mobile-friendly professional profile assistant, resume generation, and profile CRUD operations.",
)

# CORS_ALLOWED_ORIGINS: exact origins, e.g. the Vercel production URL (no trailing slash).
# CORS_ALLOWED_ORIGIN_REGEX: optional pattern for Vercel preview URLs, e.g. https://make-my-resume-.*\.vercel\.app
allowed_origins = [origin.strip().rstrip("/") for origin in os.getenv("CORS_ALLOWED_ORIGINS", "*").split(",") if origin.strip()]
dapp.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=os.getenv("CORS_ALLOWED_ORIGIN_REGEX") or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

dapp.include_router(projects.router)
dapp.include_router(skills.router)
dapp.include_router(internship.router)
dapp.include_router(certificates.router)
dapp.include_router(achievements.router)
dapp.include_router(education.router)
dapp.include_router(routes.router)
dapp.include_router(ai_chat.router)
dapp.include_router(user_details.router)
dapp.include_router(document_embeddings.router)
dapp.include_router(resume.router)


@dapp.get("/health", tags=["Health"], summary="Health check")
def health_check():
    return {"status": "ok"}


# Serve the built React frontend (see the root Dockerfile) from the same origin as the API.
FRONTEND_DIST = Path(os.getenv("FRONTEND_DIST", Path(__file__).parent / "static"))
FRONTEND_INDEX = FRONTEND_DIST / "index.html"

if FRONTEND_INDEX.is_file():
    dapp.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @dapp.get("/", include_in_schema=False)
    def frontend_index():
        return FileResponse(FRONTEND_INDEX)

    @dapp.exception_handler(StarletteHTTPException)
    async def spa_fallback(request: Request, exc: StarletteHTTPException):
        # Unmatched GETs fall through to the frontend: real files (favicon.svg, ...) are served as-is and
        # browser navigations to client-side routes (/login, /chatbot, ...) get index.html.
        # API calls keep their normal JSON errors.
        if exc.status_code == 404 and request.method == "GET":
            static_file = (FRONTEND_DIST / request.url.path.lstrip("/")).resolve()
            if static_file.is_file() and static_file.is_relative_to(FRONTEND_DIST.resolve()):
                return FileResponse(static_file)
            if "text/html" in request.headers.get("accept", ""):
                return FileResponse(FRONTEND_INDEX)
        return await http_exception_handler(request, exc)
else:

    @dapp.get("/", tags=["Health"], summary="API root")
    def root_health_check():
        return {"status": "the service is running"}
