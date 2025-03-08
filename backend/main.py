from fastapi import FastAPI
from seed import seed_user_if_needed
from app.api import router as api_router
from fastapi.middleware.cors import CORSMiddleware
from app.core.settings import settings
from app.core.startup import log_startup_config
from app.core.logging import logger

# Log configuration on startup
log_startup_config()

# Initialize database with seed data
seed_user_if_needed()

app = FastAPI(title=settings.PROJECT_NAME)

# Add CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API router
app.include_router(api_router, prefix=settings.API_V1_STR, tags=["chatbot"])

@app.get("/")
async def root():
    logger.debug("Debug test: Root endpoint called")
    logger.info("Info test: Root endpoint called")
    return {"message": "Welcome to the Chatbot API"}
