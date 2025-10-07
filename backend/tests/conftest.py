import asyncio
import os
import time
import contextlib
import aiohttp
import pytest
import uvicorn

# Ensure environment variables are loaded for tests
os.environ.setdefault("MONGODB_URL", os.getenv("MONGODB_URL", "mongodb://localhost:27017"))
os.environ.setdefault("MONGODB_DB_NAME", os.getenv("MONGODB_DB_NAME", "hospital_management"))


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for session scope to support async fixtures/tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def start_server(event_loop):
    """Start the FastAPI app with Uvicorn for the duration of the test session."""
    from src.main import app

    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="warning")
    server = uvicorn.Server(config)

    async def _serve():
        await server.serve()

    task = event_loop.create_task(_serve())

    # Wait for server to be ready by polling the root endpoint
    deadline = time.time() + 10
    async def _probe():
        async with aiohttp.ClientSession() as s:
            while time.time() < deadline:
                with contextlib.suppress(Exception):
                    async with s.get("http://127.0.0.1:8000/") as resp:
                        if resp.status in (200, 404):
                            return True
                await asyncio.sleep(0.2)
        return False

    ready = event_loop.run_until_complete(_probe())
    if not ready:
        server.should_exit = True
        event_loop.run_until_complete(asyncio.sleep(0))
        raise RuntimeError("Server failed to start for tests")

    yield

    server.should_exit = True
    # Give the server a moment to shut down gracefully
    event_loop.run_until_complete(asyncio.sleep(0.1))
    with contextlib.suppress(Exception):
        event_loop.run_until_complete(task)


@pytest.fixture()
async def session():
    """Provide an aiohttp client session to tests."""
    async with aiohttp.ClientSession() as s:
        yield s


# --- Additional simple fixtures expected by tests ---
@pytest.fixture()
def user_data():
    return {
        "email": "testuser@example.com",
        "name": "Test User",
        "phone": "1234567890",
        "password": "TestPass123",
        "role": "patient",
    }


@pytest.fixture()
def email(user_data):
    return user_data["email"]


@pytest.fixture()
def password(user_data):
    return user_data["password"]


