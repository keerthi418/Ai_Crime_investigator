from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.api.routes import router


# ============================================================
# PROJECT DIRECTORIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

FRONTEND_DIR = BASE_DIR / "frontend"
REPORTS_DIR = BASE_DIR / "reports"


# ============================================================
# CREATE REQUIRED DIRECTORIES
# ============================================================

FRONTEND_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="AI Crime Investigator",
    description=(
        "AI-assisted crime investigation, "
        "relationship analysis and reasoning system"
    ),
    version="1.0.0"
)


# ============================================================
# CORS CONFIGURATION
# ============================================================

app.add_middleware(
    CORSMiddleware,

    # Development configuration
    allow_origins=["*"],

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# API ROUTES
# ============================================================

app.include_router(
    router,
    prefix="/api"
)


# ============================================================
# REPORT FILES
# ============================================================

# Example:
# /reports/report_123.pdf
#
# will serve:
# reports/report_123.pdf

app.mount(
    "/reports",
    StaticFiles(
        directory=str(REPORTS_DIR)
    ),
    name="reports"
)


# ============================================================
# FRONTEND STATIC FILES
# ============================================================

# These files can also be accessed through:
#
# /frontend/index.html
# /frontend/login.html
# /frontend/style.css
# /frontend/script.js

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

@app.get("/", include_in_schema=False)
def root():
    """
    Open the main application.
    """

    return FileResponse(
        FRONTEND_DIR / "index.html"
    )


# ============================================================
# LOGIN PAGE
# ============================================================

@app.get("/login.html", include_in_schema=False)
def login_page():
    """
    Open the login page.
    """

    return FileResponse(
        FRONTEND_DIR / "login.html"
    )


# ============================================================
# CSS FILE
# ============================================================

@app.get("/style.css", include_in_schema=False)
def style_css():
    """
    Serve the main CSS file.
    """

    return FileResponse(
        FRONTEND_DIR / "style.css",
        media_type="text/css"
    )


# ============================================================
# JAVASCRIPT FILE
# ============================================================

@app.get("/script.js", include_in_schema=False)
def script_js():
    """
    Serve the main JavaScript file.
    """

    return FileResponse(
        FRONTEND_DIR / "script.js",
        media_type="application/javascript"
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health", include_in_schema=False)
def health_check():
    """
    Simple server health check.
    """

    return {
        "status": "online",
        "application": "AI Crime Investigator",
        "version": "1.0.0"
    }