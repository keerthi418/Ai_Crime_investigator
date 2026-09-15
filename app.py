from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.api.routes import router


Path("reports").mkdir(exist_ok=True)


app = FastAPI(
    title="AI Crime Investigator",
    description="AI-assisted crime investigation and reasoning system",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


app.include_router(
    router,
    prefix="/api"
)


app.mount(
    "/reports",
    StaticFiles(directory="reports"),
    name="reports"
)


app.mount(
    "/frontend",
    StaticFiles(directory="frontend", html=True),
    name="frontend"
)


@app.get("/")
def root():

    return FileResponse(
        "frontend/index.html"
    )