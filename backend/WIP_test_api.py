import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from app.models import Base, User
from app.schemas import ThreadCreate, MessageCreate

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test client
client = TestClient(app)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_user(db_session):
    # Create a default test user
    user = User(name="test_user")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

def test_get_user(test_user):
    response = client.get(f"/api/v1/users/{test_user.id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == test_user.id
    assert data["name"] == "test_user"
    assert data["id"] == test_user.id

def test_create_thread(test_user):
    response = client.post(
        "/api/v1/threads/",
        json={"title": "Test Thread", "user_id": test_user.id}
    )
    assert response.status_code == 200
    data = response.json()
    print(data)
    assert data["title"] == "Test Thread"
    assert data["user_id"] == test_user.id
    assert "id" in data

def test_get_thread(test_user):
    # First create a thread
    thread_response = client.post(
        "/api/v1/threads/",
        json={"title": "Test Thread", "user_id": test_user.id}
    )
    thread_id = thread_response.json()["id"]
    
    # Then get the thread
    response = client.get(f"/api/v1/threads/{thread_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Thread"
    assert data["user_id"] == test_user.id
    assert data["id"] == thread_id

def test_create_message(test_user):
    # First create a thread
    thread_response = client.post(
        "/api/v1/threads/",
        json={"title": "Test Thread", "user_id": test_user.id}
    )
    thread_id = thread_response.json()["id"]
    
    # Then create a message
    response = client.post(
        f"/api/v1/threads/{thread_id}/messages/",
        json={"content": "Hello, world!", "role": "user"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Hello, world!"
    assert data["role"] == "user"
    assert data["thread_id"] == thread_id
    assert "id" in data

def test_get_thread_messages(test_user):
    # First create a thread
    thread_response = client.post(
        "/api/v1/threads/",
        json={"title": "Test Thread", "user_id": test_user.id}
    )
    thread_id = thread_response.json()["id"]
    
    # Create a message
    client.post(
        f"/api/v1/threads/{thread_id}/messages/",
        json={"content": "Hello, world!", "role": "user"}
    )
    
    # Get messages
    response = client.get(f"/api/v1/threads/{thread_id}/messages/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "Hello, world!"
    assert data[0]["role"] == "user"
    assert data[0]["thread_id"] == thread_id

def test_get_user_threads(test_user):
    # Create multiple threads
    client.post(
        "/api/v1/threads/",
        json={"title": "Thread 1", "user_id": test_user.id}
    )
    client.post(
        "/api/v1/threads/",
        json={"title": "Thread 2", "user_id": test_user.id}
    )
    
    # Get user's threads
    response = client.get(f"/api/v1/users/{test_user.id}/threads/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(thread["user_id"] == test_user.id for thread in data)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Chatbot API"}

def test_get_nonexistent_user():
    response = client.get("/api/v1/users/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

def test_get_nonexistent_thread():
    response = client.get("/api/v1/threads/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Thread not found"

def test_create_message_in_nonexistent_thread():
    response = client.post(
        "/api/v1/threads/999/messages/",
        json={"content": "Hello, world!", "role": "user"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Thread not found"

def test_create_message_with_chatbot_response(test_user):
    # First create a thread
    thread_response = client.post(
        "/api/v1/threads/",
        json={"title": "Test Thread", "user_id": test_user.id}
    )
    thread_id = thread_response.json()["id"]
    
    # Create a message and verify both user message and bot response
    response = client.post(
        f"/api/v1/threads/{thread_id}/messages/",
        json={"content": "Hello, world!", "role": "user"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Hello, world!"
    assert data["role"] == "user"
    assert data["thread_id"] == thread_id
    
    # Verify bot response was created
    messages_response = client.get(f"/api/v1/threads/{thread_id}/messages/")
    assert messages_response.status_code == 200
    messages = messages_response.json()
    assert len(messages) == 2  # User message + bot response
    assert any(msg["role"] == "assistant" for msg in messages)

def test_get_all_users(test_user, db_session):
    # Get all users directly from the database
    users = db_session.query(User).all()
    assert users == 1
    # We should see both our test user and the seeded Alice user
    assert len(users) >= 1
    # Verify our test user exists
    assert any(user.id == test_user.id and user.name == "test_user" for user in users)
    # Log the users for debugging
    print("\nUsers in database:")
    for user in users:
        print(f"User ID: {user.id}, Name: {user.name}") 