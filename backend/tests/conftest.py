"""Pytest configuration and shared fixtures."""
import asyncio
import pytest
from typing import AsyncGenerator

try:
    import pytest_asyncio
    from httpx import AsyncClient, ASGITransport
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from app.main import app
    from app.core.database import Base, get_db
    from app.core.config import settings

    # Use SQLite for tests (no PostgreSQL needed)
    TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

    test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    TestAsyncSession = async_sessionmaker(test_engine, expire_on_commit=False)


    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestAsyncSession() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


    app.dependency_overrides[get_db] = override_get_db


    @pytest_asyncio.fixture(scope="session", autouse=True)
    async def setup_database():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


    @pytest_asyncio.fixture
    async def client() -> AsyncGenerator[AsyncClient, None]:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac


    @pytest_asyncio.fixture
    async def db() -> AsyncGenerator[AsyncSession, None]:
        async with TestAsyncSession() as session:
            yield session
            await session.rollback()


    @pytest_asyncio.fixture
    async def auth_headers(client: AsyncClient) -> dict:
        """Register a test user and return auth headers."""
        await client.post("/api/v1/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
        })
        resp = await client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword123",
        })
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

except ImportError:
    # Full web integration tests require: pip install -r requirements.txt
    pass
