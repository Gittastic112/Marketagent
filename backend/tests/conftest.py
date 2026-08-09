from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.core.config import get_settings
from app.main import app
from app.models.user import User


TEST_USER_ID = "admin_user_id_fallback"
TEST_USER = {
    "id": TEST_USER_ID,
    "email": "admin@example.com",
    "name": "Admin Fallback",
}
TEST_SEC_USER_AGENT = "Market Intelligence Test Suite sec-tests@marketintelligence.test"


@pytest.fixture(autouse=True)
def configured_test_sec_identity(monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    monkeypatch.setenv("SEC_USER_AGENT", TEST_SEC_USER_AGENT)
    get_settings.cache_clear()
    try:
        yield
    finally:
        get_settings.cache_clear()


@event.listens_for(Session, "before_flush")
def fill_test_user_id(session: Session, flush_context, instances) -> None:
    for obj in session.new:
        if hasattr(obj, "user_id") and getattr(obj, "user_id", None) is None:
            setattr(obj, "user_id", TEST_USER_ID)


@pytest.fixture(autouse=True)
def authenticated_test_user() -> Generator[None]:
    from app.api.dependencies import get_current_user

    app.dependency_overrides[get_current_user] = lambda: TEST_USER
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def db_session() -> Generator[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = TestingSessionLocal()

    # Ensure the admin user exists in the SQLite test DB
    admin_user = User(id=TEST_USER_ID, email=TEST_USER["email"], name=TEST_USER["name"])
    db.add(admin_user)
    db.commit()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def db(db_session: Session) -> Session:
    return db_session


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient]:
    def override_get_db() -> Generator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
