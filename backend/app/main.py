from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router as api_router
from app.core.config import settings

app = FastAPI(
    title="RailSync 360 — Railway Reservation & Live Projections API",
    description="Multi-cloud ADBMS architecture: AWS RDS MySQL Authoritative Core, Firebase Live Tree, Azure Cosmos DB Regional Records.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "project": "RailSync 360",
        "description": "Cloud-Based Railway Reservation, Live Seat Availability and Distributed Records System",
        "app_profile": settings.APP_PROFILE,
        "docs": "/docs",
        "api_prefix": "/api/v1"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "profile": settings.APP_PROFILE,
        "database": "MySQL 8 (Local Docker/RDS)",
        "firebase_enabled": settings.FIREBASE_ENABLED,
        "cosmos_enabled": settings.COSMOS_ENABLED
    }
