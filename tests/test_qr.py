"""The work-order QR is loaded through <img src>, which needs a namespaced SVG."""

from fastapi.testclient import TestClient

from app.main import app


def test_qr_svg_is_standalone_image():
    client = TestClient(app)
    r = client.get("/api/workorders/WO-0001/qr.svg")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/svg+xml")
    head = r.text[: r.text.index(">") + 1]
    assert 'xmlns="http://www.w3.org/2000/svg"' in head


def test_health_alias_for_cloud_run():
    client = TestClient(app)
    assert client.get("/health").json() == {"ok": True}
