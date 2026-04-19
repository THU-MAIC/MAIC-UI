from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import uvicorn
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.database import get_db, engine
from src.models import user, document, content_section, personalized_content, learning_progress, ppt_document, demo_template
from src.api import auth, pdf_processing, content, assessments, ppt_processing, demo_templates, pdf_editing, ppt_editing

# Create database tables
user.Base.metadata.create_all(bind=engine)
document.Base.metadata.create_all(bind=engine)
content_section.Base.metadata.create_all(bind=engine)
personalized_content.Base.metadata.create_all(bind=engine)
learning_progress.Base.metadata.create_all(bind=engine)
ppt_document.Base.metadata.create_all(bind=engine)
demo_template.Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Learn Your Way API is starting up...")
    yield
    # Shutdown
    print("📴 Learn Your Way API is shutting down...")

app = FastAPI(
    title="Learn Your Way API",
    description="AI-augmented textbook platform for personalized learning",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(pdf_processing.router, prefix="/api/pdf", tags=["pdf processing"])
app.include_router(ppt_processing.router, prefix="/api/ppt", tags=["ppt processing"])
app.include_router(ppt_editing.ppt_router, prefix="/api/ppt", tags=["ppt editing"])
app.include_router(ppt_editing.web_router, prefix="/api/web", tags=["ppt editing"])
app.include_router(content.router, prefix="/api/content", tags=["content"])
app.include_router(assessments.router, prefix="/api/assessments", tags=["assessments"])
app.include_router(demo_templates.router, prefix="/api/templates", tags=["demo templates"])
app.include_router(pdf_editing.web_router, prefix="/api/web", tags=["pdf editing"])
app.include_router(pdf_editing.pdf_router, prefix="/api/pdf", tags=["pdf editing"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Learn Your Way API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Learn Your Way API"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=8  # Use 8 worker processes for better concurrency
    )