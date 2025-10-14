"""
FastAPI application entry point.
Configures CORS, includes routers, and defines the main app instance.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import auth, health

# Get settings
settings = get_settings()

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
    ],
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])


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
