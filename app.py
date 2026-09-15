from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.api.routes import router


# ============================================================
# DIRECTORIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

REPORTS_DIR = BASE_DIR / "reports"
FRONTEND_DIR = BASE_DIR / "frontend"

# Create reports folder if it does not exist
REPORTS_DIR.mkdir(exist_ok=True)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="AI Crime Investigator",
    description="AI-assisted crime investigation and reasoning system",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============================================================
# API ROUTES
# ============================================================

app.include_router(
    router,
    prefix="/api"
)


# ============================================================
# REPORTS
# ============================================================

app.mount(
    "/reports",
    StaticFiles(directory=str(REPORTS_DIR)),
    name="reports"
)


# ============================================================
# FRONTEND STATIC FILES
# ============================================================

# This makes:
#
# /style.css  -> frontend/style.css
# /script.js  -> frontend/script.js
# /login.html -> frontend/login.html
# /index.html -> frontend/index.html
#
app.mount(
    "/frontend",
    StaticFiles(
        directory=str(FRONTEND_DIR),
        html=True
    ),
    name="frontend"
)


# ============================================================
# ROOT PAGE
# ============================================================

@app.get("/")
def root():
    return FileResponse(
        FRONTEND_DIR / "index.html"
    )


# ============================================================
# FRONTEND CSS
# ============================================================

@app.get("/style.css")
def style_css():
    return FileResponse(
        FRONTEND_DIR / "style.css",
        media_type="text/css"
    )


# ============================================================
# FRONTEND JAVASCRIPT
# ============================================================

@app.get("/script.js")
def script_js():
    return FileResponse(
        FRONTEND_DIR / "script.js",
        media_type="application/javascript"
    )


# ============================================================
# LOGIN PAGE
# ============================================================

@app.get("/login.html")
def login_page():
    return FileResponse(
        FRONTEND_DIR / "login.html"
    )