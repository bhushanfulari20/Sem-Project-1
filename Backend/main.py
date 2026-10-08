from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
import os
import sys

# The documented launch command runs from Backend/, while these shared modules
# live at the repository root. Add that root for both launch styles.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Detect built React frontend dist directory
FRONTEND_DIST_DIR = (
    PROJECT_ROOT / "frontend" / "dist"
    if (PROJECT_ROOT / "frontend" / "dist").is_dir()
    else PROJECT_ROOT / "Frontend" / "dist"
)

from models.schemas import ChatRequest
from utils.helpers import to_json_safe

try:
    from .worker_agent import worker_agent
    from .auditor_agent import auditor_agent
except ImportError:  # pragma: no cover - allows running main.py directly
    from worker_agent import worker_agent
    from auditor_agent import auditor_agent


# --------------------------------------------------
# SafeCart FastAPI Application
# --------------------------------------------------

app = FastAPI(
    title="SafeCart API",
    description="Self-Calibrating AI Agent for E-Commerce Compliance",
    version="1.0.0"
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

origins_env = os.getenv("ALLOWED_ORIGINS", "*").strip()
if origins_env == "*":
    allowed_origins = ["*"]
else:
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    if origins_env:
        allowed_origins.extend([o.strip() for o in origins_env.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False if "*" in allowed_origins else True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Home Route
# --------------------------------------------------

@app.get("/")
def root():
    index_file = FRONTEND_DIST_DIR / "index.html"
    if FRONTEND_DIST_DIR.is_dir() and index_file.is_file():
        return FileResponse(index_file)
    return {
        "message": "SafeCart API is running",
        "status": "OK"
    }


@app.get("/api")
def api_root():
    return {
        "message": "SafeCart API is running",
        "status": "OK"
    }


# --------------------------------------------------
# Health Check
# --------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "SafeCart API"
    }


def json_response(content: dict) -> JSONResponse:
    """Return API data after converting pandas/NumPy values to JSON values.

    CSV records can contain ``NaN`` or NumPy scalar values.  Starlette rejects
    non-finite floats while serializing a response, which otherwise turns a
    successfully handled request into an HTTP 500.
    """
    return JSONResponse(content=jsonable_encoder(to_json_safe(content)))


# --------------------------------------------------
# Chat Route
# --------------------------------------------------

@app.post("/api/chat")
@app.post("/chat", include_in_schema=False)  # Backwards compatibility for existing clients.
def chat(request: ChatRequest):

    # Check empty query
    if not request.query.strip():
        return json_response({
            "status": "ERROR",
            "response": "Customer query cannot be empty."
        })

    try:

        # ------------------------------------------
        # STEP 1: Worker AI
        # ------------------------------------------

        worker_result = worker_agent(
            query=request.query,
            order_id=request.order_id,
            product_id=request.product_id
        )


        # ------------------------------------------
        # STEP 2: Auditor AI
        # ------------------------------------------

        audit_result = auditor_agent(
            query=request.query,
            order_id=request.order_id,
            product_id=request.product_id,
            worker_result=worker_result
        )


        # ------------------------------------------
        # STEP 3: Return Safe Response
        # ------------------------------------------

        return json_response({
            "status": audit_result.get(
                "status",
                "ERROR"
            ),

            "response": audit_result.get(
                "response",
                "SafeCart could not generate a response."
            ),

            "worker_response": worker_result,

            "audit": audit_result
        })


    except Exception as e:

        return {
            "status": "ERROR",
            "response": "An internal SafeCart error occurred.",
            "error": str(e)
        }


# The React app is built into Frontend/dist. Mount it last so API and docs
# routes (/api, /health, /docs) are not intercepted by the static file handler.
if FRONTEND_DIST_DIR.is_dir():
    app.mount(
        "/",
        StaticFiles(directory=FRONTEND_DIST_DIR, html=True),
        name="frontend",
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("Backend.main:app", host="0.0.0.0", port=port, reload=False)

