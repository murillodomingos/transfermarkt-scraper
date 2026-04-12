import io
import json
from pathlib import Path

import pytest

from tfscrap.spiders.base import BaseSpider


class DummySpider(BaseSpider):
    name = "dummy"

    def parse(self, response, **kwargs):
        yield {}


@pytest.fixture
def parents_jsonl():
    return "\n".join(
        [
            json.dumps({"type": "competition", "href": "/wettbewerbe/gb1"}),
            json.dumps({"type": "competition", "href": "/wettbewerbe/es1"}),
        ]
    )


class TestReadParents:
    def test_reads_parents_from_stdin(self, monkeypatch, parents_jsonl):
        monkeypatch.setattr("sys.stdin", io.StringIO(parents_jsonl))
        spider = DummySpider()
        parents = list(spider.read_parents())
        assert len(parents) == 2
        assert parents[0]["href"] == "/wettbewerbe/gb1"
        assert parents[1]["href"] == "/wettbewerbe/es1"

    def test_reads_parents_from_file(self, tmp_path: Path, parents_jsonl: str):
        f = tmp_path / "parents.jsonl"
        f.write_text(parents_jsonl)
        spider = DummySpider(parents=str(f))
        parents = list(spider.read_parents())
        assert len(parents) == 2

    def test_skips_blank_lines(self, monkeypatch):
        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO('{"href": "/a"}\n\n   \n{"href": "/b"}\n'),
        )
        parents = list(DummySpider().read_parents())
        assert [p["href"] for p in parents] == ["/a", "/b"]


class TestStartRequests:
    def test_builds_requests_with_base_url(self, monkeypatch, parents_jsonl):
        monkeypatch.setattr("sys.stdin", io.StringIO(parents_jsonl))
        spider = DummySpider()
        requests = list(spider.start_requests())
        assert len(requests) == 2
        assert requests[0].url == "https://www.transfermarkt.com/wettbewerbe/gb1"
        assert requests[1].url == "https://www.transfermarkt.com/wettbewerbe/es1"

    def test_attaches_parent_to_request_meta(self, monkeypatch, parents_jsonl):
        monkeypatch.setattr("sys.stdin", io.StringIO(parents_jsonl))
        spider = DummySpider()
        req = next(iter(spider.start_requests()))
        assert req.meta["parent"]["href"] == "/wettbewerbe/gb1"

    def test_custom_base_url(self, monkeypatch, parents_jsonl):
        monkeypatch.setattr("sys.stdin", io.StringIO(parents_jsonl))
        spider = DummySpider(base_url="https://www.transfermarkt.de")
        req = next(iter(spider.start_requests()))
        assert req.url.startswith("https://www.transfermarkt.de/")

    def test_sends_browser_like_headers(self, monkeypatch, parents_jsonl):
        monkeypatch.setattr("sys.stdin", io.StringIO(parents_jsonl))
        spider = DummySpider()
        req = next(iter(spider.start_requests()))
        ua = req.headers.get("User-Agent", b"").decode()
        assert "Mozilla" in ua or "tfscrap" in ua
        assert req.headers.get("Accept-Language") is not None
