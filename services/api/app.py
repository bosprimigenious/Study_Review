"""FastAPI application for Study Review."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core import config as _config  # noqa: F401 — ensure scripts/ on sys.path
from .routes import agent, courses, exams, materials, mistakes, sessions

app = FastAPI(
    title="Study Review API",
    version="0.4.0",
    description="CLI-backed exam review API for local course materials",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(courses.router)
app.include_router(materials.router)
app.include_router(exams.router)
app.include_router(sessions.router)
app.include_router(mistakes.router)
app.include_router(agent.router)


@app.get("/health")
def health() -> dict[str, str | int | bool]:
    from .core.config import COURSES_ROOT

    course_dirs = [
        d.name
        for d in COURSES_ROOT.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ] if COURSES_ROOT.exists() else []
    return {
        "status": "ok",
        "version": "0.4.0",
        "courses_root": str(COURSES_ROOT),
        "courses_count": len(course_dirs),
    }
