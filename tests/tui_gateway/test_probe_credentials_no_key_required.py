"""Regression test for issue #20815.

Local providers (llama.cpp / llama-swap / Ollama) carry the placeholder
api_key value ``"no-key-required"``. The dashboard credential probe must
treat that as a valid credential, not a missing one.
"""

from types import SimpleNamespace

from tui_gateway.server import _probe_credentials


def test_probe_credentials_returns_empty_for_no_key_required():
    """Local provider with placeholder key produces no warning."""
    agent = SimpleNamespace(api_key="no-key-required", provider="custom")
    assert _probe_credentials(agent) == ""


def test_probe_credentials_warns_on_empty_key():
    """Genuinely missing credential still produces a warning."""
    agent = SimpleNamespace(api_key="", provider="openai")
    warning = _probe_credentials(agent)
    assert "openai" in warning
    assert "No API key" in warning


def test_probe_credentials_returns_empty_for_real_key():
    """A real credential produces no warning."""
    agent = SimpleNamespace(api_key="sk-real-key", provider="openai")
    assert _probe_credentials(agent) == ""
