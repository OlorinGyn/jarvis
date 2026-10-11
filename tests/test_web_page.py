"""The page and its files are never served from a stale cache (R28)."""

from fastapi.testclient import TestClient

from jarvis import web


def test_the_page_names_its_files_by_version_and_is_never_cached(monkeypatch):
    monkeypatch.setattr(web, "_version", "v2026.10.11-3-gabc1234")
    client = TestClient(web.app)
    page = client.get("/")
    assert page.headers["cache-control"] == "no-cache"
    assert '"/static/app.js?v=v2026.10.11-3-gabc1234"' in page.text
    assert '"/static/style.css?v=v2026.10.11-3-gabc1234"' in page.text
    script = client.get("/static/app.js?v=v2026.10.11-3-gabc1234")
    assert script.status_code == 200 and script.headers["cache-control"] == "no-cache"
    again = client.get("/static/app.js", headers={"If-None-Match": script.headers["etag"]})
    assert again.status_code == 304
