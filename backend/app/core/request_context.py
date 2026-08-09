from contextvars import ContextVar
from uuid import UUID, uuid4


request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)


def normalize_request_id(value: str | None) -> str:
    if value:
        try:
            parsed = UUID(value)
        except (ValueError, AttributeError):
            pass
        else:
            return str(parsed)
    return str(uuid4())


def get_request_id() -> str | None:
    return request_id_context.get()
