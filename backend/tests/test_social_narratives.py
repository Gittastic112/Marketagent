import pytest
from fastapi.testclient import TestClient
from sqlmodel.pool import StaticPool
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

def test_social_post_crud(client: TestClient):
    # Create
    post_data = {
        "platform": "Substack",
        "source_url": "https://substack.com/post/123",
        "author": "Analyst A",
        "raw_text": "Company X is experiencing strong headwinds.",
        "published_at": "2026-05-28T10:00:00Z"
    }
    response = client.post("/social-posts", json=post_data)
    assert response.status_code == 201
    post = response.json()
    assert post["platform"] == "Substack"
    assert "content_hash" in post

    post_id = post["id"]

    # Read
    response = client.get(f"/social-posts/{post_id}")
    assert response.status_code == 200
    assert response.json()["author"] == "Analyst A"

    # Update
    response = client.patch(f"/social-posts/{post_id}", json={"author": "Analyst B"})
    assert response.status_code == 200
    assert response.json()["author"] == "Analyst B"

    # Delete
    response = client.delete(f"/social-posts/{post_id}")
    assert response.status_code == 204
    
    # Verify Delete
    response = client.get(f"/social-posts/{post_id}")
    assert response.status_code == 404

def test_narrative_cluster_crud(client: TestClient):
    # Create
    cluster_data = {
        "name": "Headwinds in Sector",
        "description": "General slowdown in spending"
    }
    response = client.post("/narrative-clusters", json=cluster_data)
    assert response.status_code == 201
    cluster = response.json()
    assert cluster["name"] == "Headwinds in Sector"
    
    cluster_id = cluster["id"]
    
    # Add a claim
    claim_data = {
        "cluster_id": cluster_id,
        "claim_text": "Spending is down 10%"
    }
    response = client.post("/narrative-claims", json=claim_data)
    assert response.status_code == 201
    assert response.json()["claim_text"] == "Spending is down 10%"
