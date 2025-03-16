from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from fastapi.routing import APIRouter

from app.config import CORS_ALLOW_ORIGINS
from app.routes import auth, goals, motivations, qrcode, search

# Define API version
API_VERSION = "v1"

app = FastAPI(
    title="Goal Tracker API",
    description="An application that allows users to set and track their goals, motivated by personal incentives. Goals can be accessed securely and conveniently by generating a QR code, which only the user can scan.",
    version=API_VERSION,
    docs_url=f"/api/{API_VERSION}/docs",
    redoc_url=f"/api/{API_VERSION}/redoc",
    contact={
        "name": "Rirash",
        "url": "https://rirash.com",
        "email": "codesavvylabs@gmail.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    terms_of_service="https://sataplan.com/terms",
)

app.add_middleware(
    GZipMiddleware,
    minimum_size=100,
)

origins = ["http://localhost:5173", CORS_ALLOW_ORIGINS]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a versioned router
versioned_router = APIRouter(prefix=f"/api/{API_VERSION}")


@app.get("/")
async def health():
    return {"message": "Healthy"}


# Include routers with version prefix
versioned_router.include_router(
    auth.router,
)
versioned_router.include_router(
    goals.router,
)
versioned_router.include_router(
    motivations.router,
)
versioned_router.include_router(
    qrcode.router,
)
versioned_router.include_router(
    search.router,
)
versioned_router.include_router(
    auth.user_router,
)

# Include the versioned router in the main app
app.include_router(versioned_router)
