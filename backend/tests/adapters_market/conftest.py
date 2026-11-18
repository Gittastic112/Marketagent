"""No live provider calls in market adapter tests. Payloads are Mock Data unless named captured_sample."""
import socket
import pytest


@pytest.fixture(autouse=True)
def no_adapter_network(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Unexpected live network call in market adapter test")
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
