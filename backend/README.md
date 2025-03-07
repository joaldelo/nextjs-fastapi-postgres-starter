# Chatbot Backend Service

This is the backend service for a chatbot application that manages conversation threads and messages between users and the chatbot.

## Features

- User management
- Conversation thread management
- Message handling between users and chatbot
- RESTful API endpoints
- Comprehensive test coverage

## API Endpoints

### Users
- `POST /api/v1/users/` - Create a new user
- `GET /api/v1/users/{user_id}` - Get user details

### Threads
- `POST /api/v1/threads/` - Create a new conversation thread
- `GET /api/v1/threads/{thread_id}` - Get thread details
- `GET /api/v1/users/{user_id}/threads/` - Get all threads for a user

### Messages
- `POST /api/v1/threads/{thread_id}/messages/` - Create a new message in a thread
- `GET /api/v1/threads/{thread_id}/messages/` - Get all messages in a thread

## Setup

1. Install dependencies:
```bash
poetry install
```

2. Start PostgreSQL:
```bash
brew services start postgresql
```

3. Run the development server:
```bash
poetry run uvicorn main:app --reload
```

4. Run tests:
```bash
poetry run pytest
```

## API Documentation

Once the server is running, you can access:
- Interactive API docs (Swagger UI): http://localhost:8000/docs
- Alternative API docs (ReDoc): http://localhost:8000/redoc

## Development vs Production Dependencies

- Development: Uses `psycopg2-binary` for easier setup
- Production: Uses `psycopg2` with system PostgreSQL libraries

To install production dependencies:
```bash
poetry install --only main --extras production
```

## Data Models

### User
- `id`: Primary key
- `name`: User's name

### Thread
- `id`: Primary key
- `title`: Thread title
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp
- `user_id`: Foreign key to User

### Message
- `id`: Primary key
- `content`: Message content
- `role`: Message role ('user' or 'assistant')
- `created_at`: Creation timestamp
- `thread_id`: Foreign key to Thread 