import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.core.security import get_password_hash, create_access_token
from app.repositories.user_repository import UserRepository
from app.repositories.athlete_repository import AthleteRepository

# In-memory SQLite for fast isolated testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user_a(db_session: AsyncSession):
    repo = UserRepository(db_session)
    user = await repo.create(
        email="usera@example.com",
        hashed_password=get_password_hash("Password123!"),
        full_name="User Alpha"
    )
    token = create_access_token(subject=str(user.id))
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest_asyncio.fixture
async def test_user_b(db_session: AsyncSession):
    repo = UserRepository(db_session)
    user = await repo.create(
        email="userb@example.com",
        hashed_password=get_password_hash("Password123!"),
        full_name="User Beta"
    )
    token = create_access_token(subject=str(user.id))
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}
