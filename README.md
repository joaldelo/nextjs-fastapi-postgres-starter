## Project Overview

This is a real-time chat application built with a modern tech stack:
- Frontend: Next.js with TypeScript
- Backend: FastAPI (Python)
- Database: PostgreSQL
- Real-time Communication: WebSocket
- Containerization: Docker

The application demonstrates a production-ready architecture for building real-time chat applications with AI capabilities.

## System Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Next.js   │     │   FastAPI   │     │ PostgreSQL  │
│  Frontend   │◄───►│   Backend   │◄───►│  Database   │
└─────────────┘     └─────────────┘     └─────────────┘
      ▲                    ▲                   ▲
      │                    │                   │
      │              ┌──────────┐             │
      └──────────────┤WebSocket │─────────────┘
                     └──────────┘
```

### Key Components

1. Frontend (Next.js):
   - Modern React with TypeScript
   - Real-time WebSocket client
   - Responsive chat interface
   - Thread management UI

2. Backend (FastAPI):
   - RESTful API endpoints
   - WebSocket server
   - Database ORM (SQLAlchemy)
   - AI chat integration ( dummy random text chat bot)

3. Database (PostgreSQL):
   - Message persistence
   - Thread management
   - User data storage

## Database Schema

```sql
Table thread {
  id          integer [pk]
  created_at  timestamp
  updated_at  timestamp
}

Table message {
  id          integer [pk]
  thread_id   integer [ref: > thread.id]
  content     text
  role        string    // 'user' or 'assistant'
  created_at  timestamp
}
```

## Development Guide

### Project Structure
```
├── frontend/                 # Next.js frontend
│   ├── app/                 # Next.js App Router
│   │   ├── components/     # React components
│   │   ├── services/      # API and WebSocket services
│   │   ├── types/        # TypeScript type definitions
│   │   ├── page.tsx      # Main application page
│   │   ├── layout.tsx    # Root layout component
│   │   └── globals.css   # Global styles
│   ├── public/            # Static assets
│   └── package.json       # Frontend dependencies
├── backend/                 # FastAPI backend
│   ├── app/               # Application package
│   │   ├── core/         # Core functionality (settings, database, logging)
│   │   ├── api.py       # REST API endpoints
│   │   ├── websocket.py # WebSocket implementation
│   │   ├── models.py    # SQLAlchemy models
│   │   ├── schemas.py   # Pydantic schemas
│   │   ├── crud.py      # Database operations
│   │   └── chatbot.py   # AI chat implementation
│   ├── main.py           # Application entry point
│   └── pyproject.toml    # Backend dependencies
└── docker-compose.yml      # Docker services configuration
```

### Environment Variables

Backend (`.env`):
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres
```

Frontend (`.env.local`):
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Running the Application


## Required Software

1. Python
2. Node.js
3. Docker and Docker Compose
4. [Poetry](https://python-poetry.org/docs/#installation)
5. Postgres libpq header files (e.g. `apt install libpq-dev` on Ubuntu, `brew install postgresql` on macOS)

### First-Time Setup

1. `cd` into `backend` and run `poetry install`.
2. `cd` into `frontend` and run `npm install`.

### Running the Application Locally ( old way )

1. From the root directory, run `docker compose up`.
2. In a separate terminal, `cd` into `backend` and run `poetry run uvicorn main:app --reload`.
3. In a separate terminal, `cd` into `frontend` and run `npm run dev`.

### Running the Application in Containers (recommended)

To run the entire application stack (frontend, backend, and database) in containers:

1. Make sure Docker and Docker Compose are installed and running on your system.
2. From the root directory, run:
   ```bash
   docker compose up --build
   ```
3. Wait for all services to start up. You can access:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Database: Available on localhost:5432

To stop the containers, press Ctrl+C in the terminal or run:
```bash
docker compose down
```


## Using the Application

Once the application is running, you can access it through your web browser at http://localhost:3000. Here's how to use it:

1. The application comes with a single pre-configured user account that you can use to interact with the chat system.

2. To start a new conversation:
   - Click on the "New Chat" button
   - A new chat session will be created with our AI bot
   - Start typing your messages in the chat input field
   - Press Enter or click the send button to send your message

3. The AI bot will respond to your messages in real-time, creating an interactive conversation experience.

## API Documentation

When the backend is running, you can access the auto-generated API documentation in two ways:

1. Swagger UI (OpenAPI): 
   - Visit http://localhost:8000/docs
   - This provides an interactive interface to explore and test all REST API endpoints
   - You can see request/response schemas and try out the endpoints directly

Note: WebSocket endpoints (used for real-time chat) are not visible in the Swagger  documentation because they use a different protocol (WebSocket instead of HTTP). WebSocket connections are handled at the `/ws` endpoint.

## WebSocket Chat Architecture

The real-time chat functionality is implemented using WebSocket protocol. Here's how the chat flow works:

1. Connection Setup:
   - Frontend establishes a WebSocket connection to `/api/v1/ws/threads/{thread_id}`
   - Backend validates database session and thread existence
   - A singleton WebSocketService manages all connections

2. Message Flow:
   ```
   [Frontend] <----WebSocket----> [Backend] <-----> [SimpleChatbot]
      |                              |                   |
   User Input --> JSON Message --> Store in DB --> Generate Response
      |                              |                   |
   Display <---- JSON Message <-- Store in DB <-- Return Response
   ```

3. Message Format:
   ```typescript
   // Frontend to Backend (Send)
   {
     "content": string,      // The user's message
   }

   // Backend to Frontend (Receive)
   {
     "type": "message",
     "data": {
       "id": number,         // Message ID from database
       "thread_id": number,  // Thread identifier
       "content": string,    // Message content
       "role": string,       // "user" or "assistant"
       "created_at": string  // ISO format timestamp
     }
   }
   ```

4. Implementation Details:
   - Frontend uses a singleton WebSocketService class for connection management
   - Backend uses FastAPI WebSocket endpoints with a ConnectionManager
   - Messages are persisted in PostgreSQL before broadcasting
   - Each thread maintains its own set of WebSocket connections
   - Supports multiple clients viewing the same thread
   - Optimistic updates for better UX (temporary messages shown before confirmation)
   - Standardized error handling and response formatting
   - Automatic cleanup of failed connections
   - Improved type safety with comprehensive type hints

5. Connection Lifecycle:
   ```typescript
   // Connection URL
   ws://localhost:8000/api/v1/ws/threads/${threadId}

   // Connection States
   - Connecting: Initial WebSocket connection attempt (5s timeout)
   - Connected: Successfully connected to thread
   - Reconnecting: Attempting to reconnect (exponential backoff)
   - Disconnected: Connection closed or failed

   // Error Codes
   - 4003: Database session inactive
   - 4004: Thread not found
   - 4005: Critical connection error
   ```

6. Error Handling & Recovery:
   - Automatic reconnection with exponential backoff (up to 5 attempts)
   - Maximum backoff delay of 10 seconds
   - Connection timeout after 5 seconds
   - Clean disconnection when switching threads
   - Thread validation on connection
   - Message validation and error logging
   - Optimistic message rollback on errors
   - Standardized error responses with error codes
   - Graceful handling of failed connections

7. Advanced Features:
   - Connection pooling per thread
   - Message persistence in database
   - Conversation history tracking
   - Thread-based message broadcasting
   - Automatic cleanup of disconnected clients
   - Optimistic UI updates
   - Message deduplication
   - Type-safe message handling
   - Comprehensive error logging
   - Standardized response formatting

8. Example Frontend Usage:
   ```typescript
   const wsService = WebSocketService.getInstance();
   
   // Connect to a thread
   await wsService.connect(threadId, (message: Message) => {
     // Handle incoming message
     console.log('Received:', message);
   });

   // Send a message
   await wsService.sendMessage({
     content: "Hello, how are you?"
   });

   // Clean disconnection
   await wsService.disconnect();
   ```

 