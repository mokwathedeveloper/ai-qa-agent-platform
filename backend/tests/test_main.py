import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.main import app, get_db
from backend.database.core import create_db_and_tables
from backend.database.models import Base
from unittest.mock import patch

# Setup the in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    create_db_and_tables(engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    # connect to the database
    connection = engine.connect()
    # begin a non-ORM transaction
    trans = connection.begin()
    # bind an individual Session to the connection
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        # rollback - everything that happened with the
        # Session above (including calls to commit())
        # is rolled back.
        trans.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client_with_db(db_session):
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    try:
        yield client
    finally:
        del app.dependency_overrides[get_db]


def test_health_check(client_with_db):
    response = client_with_db.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "1.0.0"}

@patch("backend.main.execute_tests_task")
@patch("backend.main.get_current_user")
def test_run_tests_trigger(mock_get_current_user, mock_execute_tests, client_with_db, db_session):
    # Mock the current user
    from backend.database.models import User
    mock_user = User(id=1, username="testuser", email="test@example.com")
    mock_get_current_user.return_value = mock_user
    
    # Now test the run-tests endpoint
    response = client_with_db.post("/run-tests", 
        json={
            "test_url": "https://example.com",
            "cycle_overview": "My Overview",
            "testing_instructions": "My Instructions"
        },
        headers={"Authorization": "Bearer fake-token"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] == "PENDING"
    
    mock_execute_tests.assert_called_once()


