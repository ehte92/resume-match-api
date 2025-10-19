"""
FastAPI application entry point.
Configures CORS, includes routers, and defines the main app instance.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import get_settings
from app.middleware.timing import TimingMiddleware
from app.routers import analysis, auth, health, resume, user

# Get settings
settings = get_settings()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app instance
app = FastAPI(
    title="AI Resume Optimizer API",
    description="Backend API for AI-powered resume optimization and ATS checking",
    version="1.0.0",
    contact={"name": "Resume Optimizer Team", "email": "support@resumeoptimizer.com"},
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    openapi_tags=[
        {"name": "health", "description": "Health check endpoints for monitoring"},
        {
            "name": "authentication",
            "description": "User authentication and authorization endpoints",
        },
        {
            "name": "users",
            "description": "User profile and settings management endpoints",
        },
        {
            "name": "resumes",
            "description": "Resume upload, management, and retrieval endpoints",
        },
        {
            "name": "analyses",
            "description": "Resume analysis endpoints - compare resumes against job descriptions",
        },
    ],
)

# Register rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure middleware (order matters - last added is executed first)
# 1. CORS - handles cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. GZip compression - compresses responses > 1KB
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 3. Timing - tracks request processing time
app.add_middleware(TimingMiddleware)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(user.router, prefix="/api/users", tags=["users"])
app.include_router(resume.router, prefix="/api/resumes", tags=["resumes"])
app.include_router(analysis.router, prefix="/api/analyses", tags=["analyses"])


@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler.
    Runs when the server starts.
    """
    print("Starting AI Resume Optimizer API")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug mode: {settings.DEBUG}")
    print(f"CORS origins: {settings.CORS_ORIGINS}")
    print(f"API documentation: http://{settings.HOST}:{settings.PORT}/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event handler.
    Runs when the server stops.
    """
    print("Shutting down AI Resume Optimizer API")


@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint that provides API information.

    Returns:
        dict: API welcome message and links
    """
    return {
        "message": "Welcome to AI Resume Optimizer API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


# TODO: Add global exception handlers (optional for Phase 3)
# from fastapi.exceptions import RequestValidationError
# from fastapi import Request
#
# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request: Request, exc: RequestValidationError):
#     return JSONResponse(
#         status_code=422,
#         content={"detail": exc.errors()},
#     )
