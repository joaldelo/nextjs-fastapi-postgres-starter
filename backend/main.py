from fastapi import FastAPI
from seed import seed_user_if_needed
from api import router as api_router

seed_user_if_needed()

app = FastAPI(title="Chatbot API", description="Backend API for chatbot application")

# Include the API router
app.include_router(api_router, prefix="/api/v1", tags=["chatbot"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Chatbot API"}
