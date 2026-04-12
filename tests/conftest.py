from pathlib import Path

import pytest
from scrapy.http import HtmlResponse, Request

FIXTURES = Path(__file__).parent / "fixtures"


def load_response(name: str, url: str, parent: dict | None = None) -> HtmlResponse:
    body = (FIXTURES / name).read_bytes()
    request = Request(url=url, meta={"parent": parent or {}})
    return HtmlResponse(url=url, body=body, encoding="utf-8", request=request)


@pytest.fixture
def fixture_response():
    return load_response
