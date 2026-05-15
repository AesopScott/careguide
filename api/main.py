from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from routers import health, ai, family_groups, parents, medications, session_notes

load_dotenv()

app = FastAPI(
    title="CareGuide API",
    version="0.1.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") == "development" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(ai.router, prefix="/ai", tags=["AI"])
app.include_router(family_groups.router, prefix="/family-groups", tags=["Family Groups"])
app.include_router(parents.router, prefix="/parents", tags=["Parents"])
app.include_router(medications.router, prefix="/medications", tags=["Medications"])
app.include_router(session_notes.router, prefix="/session-notes", tags=["Session Notes"])
