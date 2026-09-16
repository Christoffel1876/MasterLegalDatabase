"""Test staged ordinary modules without installing them or permitting real transport."""
from pathlib import Path
import sys
import pytest

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from load_proposed import load
watch = load()

@pytest.fixture(autouse=True)
def no_public_transport(monkeypatch):
    """Default transports must be mocked explicitly by each offline test."""
    import socket
    # HTTP helper transport tests replace getaddrinfo/connect with local fakes.
    def refuse(*args, **kwargs):
        raise AssertionError('Unmocked network prohibited in this offline suite')
    monkeypatch.setattr(socket, 'getaddrinfo', refuse)
