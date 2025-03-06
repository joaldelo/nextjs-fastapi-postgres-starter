import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from models import Base
from schemas import ThreadCreate, MessageCreate

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


def test_get_user():
    # First create a user
    create_response = client.post(
        "/api/v1/users/",
        json={"name": "test_user"}
    )
    user_id = create_response.json()["id"]
    
    # Then get the user
    response = client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test_user"
    assert data["id"] == user_id

def test_create_thread():
    # First create a user
    user_response = client.post(
        "/api/v1/users/",
        json={"name": "test_user"}
    )
    user_id = user_response.json()["id"]
    
    # Then create a thread
    response = client.post(
        "/api/v1/threads/",
        json={"title": "Test Thread", "user_id": user_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Thread"
    assert data["user_id"] == user_id
    assert "id" in data

def test_get_thread():
    # First create a user and thread
    user_response = client.post(
        "/api/v1/users/",
        json={"name": "test_user"}
    )
    user_id = user_response.json()["id"]
    
    thread_response = client.post(
        "/api/v1/threads/",
        json={"title": "Test Thread", "user_id": user_id}
    )
    thread_id = thread_response.json()["id"]
    
    # Then get the thread
    response = client.get(f"/api/v1/threads/{thread_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Thread"
    assert data["user_id"] == user_id
    assert data["id"] == thread_id

def test_create_message():
    # First create a user and thread
    user_response = client.post(
        "/api/v1/users/",
        json={"name": "test_user"}
    )
    user_id = user_response.json()["id"]
    
    thread_response = client.post(
        "/api/v1/threads/",
        json={"title": "Test Thread", "user_id": user_id}
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

def test_get_thread_messages():
    # First create a user and thread
    user_response = client.post(
        "/api/v1/users/",
        json={"name": "test_user"}
    )
    user_id = user_response.json()["id"]
    
    thread_response = client.post(
        "/api/v1/threads/",
        json={"title": "Test Thread", "user_id": user_id}
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

def test_get_user_threads():
    # First create a user
    user_response = client.post(
        "/api/v1/users/",
        json={"name": "test_user"}
    )
    user_id = user_response.json()["id"]
    
    # Create multiple threads
    client.post(
        "/api/v1/threads/",
        json={"title": "Thread 1", "user_id": user_id}
    )
    client.post(
        "/api/v1/threads/",
        json={"title": "Thread 2", "user_id": user_id}
    )
    
    # Get user's threads
    response = client.get(f"/api/v1/users/{user_id}/threads/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(thread["user_id"] == user_id for thread in data) 