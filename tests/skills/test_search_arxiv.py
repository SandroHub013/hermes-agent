"""Tests for skills/research/arxiv/scripts/search_arxiv.py.

Focus: the CLI must fail gracefully (clean stderr message + non-zero exit)
on network and parse errors instead of dumping a raw Python traceback.
"""

import io
import sys
import urllib.error
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "skills" / "research" / "arxiv" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import search_arxiv  # noqa: E402


class TestFetchNetworkErrors:
    def test_http_error_exits_cleanly(self, monkeypatch, capsys):
        def raise_http(*args, **kwargs):
            raise urllib.error.HTTPError(
                url="https://export.arxiv.org/api/query",
                code=503,
                msg="Service Unavailable",
                hdrs=None,
                fp=io.BytesIO(b""),
            )

        monkeypatch.setattr(search_arxiv.urllib.request, "urlopen", raise_http)
        with pytest.raises(SystemExit) as exc:
            search_arxiv._fetch("https://export.arxiv.org/api/query?x=1")
        assert exc.value.code == 1
        err = capsys.readouterr().err
        assert "503" in err
        assert "arXiv API error" in err

    def test_url_error_exits_cleanly(self, monkeypatch, capsys):
        def raise_url(*args, **kwargs):
            raise urllib.error.URLError("Name or service not known")

        monkeypatch.setattr(search_arxiv.urllib.request, "urlopen", raise_url)
        with pytest.raises(SystemExit) as exc:
            search_arxiv._fetch("https://export.arxiv.org/api/query?x=1")
        assert exc.value.code == 1
        assert "Network error contacting arXiv" in capsys.readouterr().err

    def test_timeout_exits_cleanly(self, monkeypatch, capsys):
        def raise_timeout(*args, **kwargs):
            raise TimeoutError("timed out")

        monkeypatch.setattr(search_arxiv.urllib.request, "urlopen", raise_timeout)
        with pytest.raises(SystemExit) as exc:
            search_arxiv._fetch("https://export.arxiv.org/api/query?x=1")
        assert exc.value.code == 1
        assert "Network error contacting arXiv" in capsys.readouterr().err


class TestSearchParseError:
    def test_malformed_response_exits_cleanly(self, monkeypatch, capsys):
        # arXiv occasionally returns a non-XML error page; that must not crash.
        monkeypatch.setattr(search_arxiv, "_fetch", lambda url: b"<html>oops")
        with pytest.raises(SystemExit) as exc:
            search_arxiv.search(query="anything")
        assert exc.value.code == 1
        assert "Could not parse arXiv response" in capsys.readouterr().err


class TestSearchSuccess:
    _ATOM = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">
  <opensearch:totalResults>1</opensearch:totalResults>
  <entry>
    <id>http://arxiv.org/abs/2402.03300v2</id>
    <title>A Test Paper</title>
    <summary>This is a summary.</summary>
    <published>2024-02-05T00:00:00Z</published>
    <updated>2024-02-06T00:00:00Z</updated>
    <author><name>Jane Doe</name></author>
    <category term="cs.AI"/>
  </entry>
</feed>"""

    def test_renders_entry(self, monkeypatch, capsys):
        monkeypatch.setattr(search_arxiv, "_fetch", lambda url: self._ATOM)
        search_arxiv.search(query="test")
        out = capsys.readouterr().out
        assert "A Test Paper" in out
        assert "2402.03300" in out
        assert "Jane Doe" in out
        assert "cs.AI" in out
