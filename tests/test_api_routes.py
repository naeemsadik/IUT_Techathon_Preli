"""FastAPI route tests."""

from fastapi.testclient import TestClient


def test_get_status(api_client: TestClient) -> None:
    response = api_client.get("/api/status")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["total_wattage"] == 1430


def test_get_room(api_client: TestClient) -> None:
    response = api_client.get("/api/room/Drawing%20Room")

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Drawing Room"


def test_get_unknown_room_returns_404(api_client: TestClient) -> None:
    response = api_client.get("/api/room/Server%20Room")

    assert response.status_code == 404


def test_get_usage(api_client: TestClient) -> None:
    response = api_client.get("/api/usage")

    assert response.status_code == 200
    assert response.json()["data"]["weekly_kwh"] == 126.7


def test_get_health(api_client: TestClient) -> None:
    response = api_client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ok"


