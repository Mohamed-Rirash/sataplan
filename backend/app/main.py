from fastapi import FastAPI
from app.routes import auth, goals, motivations, qrcode,search
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from app.config import CORS_ALLOW_ORIGINS

app = FastAPI(
    title="Goal Tracker API",
description="An application that allows users to set and track their goals, motivated by personal incentives. Goals can be accessed securely and conveniently by generating a QR code, which only the user can scan.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
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

origins = [
    CORS_ALLOW_ORIGINS
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/health")
async def health():
    return {"message": "Healthy"}

app.include_router(auth.router)
app.include_router(goals.router)
app.include_router(motivations.router)
app.include_router(qrcode.router)
app.include_router(search.router)
app.include_router(auth.guest_router)

# app.include_router(qrcodenew.router)
#
#
