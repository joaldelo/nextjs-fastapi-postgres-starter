from fastapi import FastAPI, WebSocket
from seed import seed_user_if_needed
from app.api import router as api_router
from app.websocket import handle_websocket
from fastapi.middleware.cors import CORSMiddleware

seed_user_if_needed()

app = FastAPI(title="Chatbot API", description="Backend API for chatbot application")

# Add CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #TODO: Change to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API router
app.include_router(api_router, prefix="/api/v1", tags=["chatbot"])

# WebSocket endpoint
@app.websocket("/ws/threads/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: int):
    await handle_websocket(websocket, thread_id)

@app.get("/")
async def root():
    return {"message": "Welcome to the Chatbot API"}
