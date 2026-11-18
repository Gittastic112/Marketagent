"""Opt-in disposable browser fixture; never copied into the application image."""
import os
import time

from sqlalchemy.engine import make_url

if os.getenv("APP_ENV") != "test" or os.getenv("AI_DEMO_MODE") != "true" or not make_url(os.environ["DATABASE_URL"]).database.endswith("_e2e"):
    raise RuntimeError("Delayed research fixture requires an explicitly isolated test database and Mock Data")

from app.main import app  # noqa: E402,F401
from app.providers.mock_provider import MockAIProvider  # noqa: E402

original = MockAIProvider.generate_chat_response


def delayed(self, messages, context=""):
    if messages[-1]["content"] == "Mock Data delayed response beyond the ordinary proxy deadline":
        time.sleep(16)
    return original(self, messages, context)


MockAIProvider.generate_chat_response = delayed
