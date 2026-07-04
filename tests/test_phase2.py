"""Phase 2 integration tests for ingestion, alerts, and WebSockets."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from backend.app.config import get_settings
from backend.app.main import create_app
from backend.app.state import DEVICE_MANIFEST


@pytest.fixture
def phase2_client(tmp_path, monkeypatch):
    """Return a test client backed by the real Phase 2 stack."""

    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "phase2.db"))
    monkeypatch.setenv("DURATION_THRESHOLD_SECONDS", "0")
    monkeypatch.setenv("ALERT_SWEEP_INTERVAL_SECONDS", "3600")
    get_settings.cache_clear()
    app = create_app()
    with TestClient(app) as client:
        yield client
    get_settings.cache_clear()


def _state_change_payload(
    device_id: str,
    room: str,
    device_type: str,
    status: str,
    power_draw_w: int,
    sequence: int = 1,
) -> dict:
    return {
        "message_type": "state_change",
        "source_id": f"esp32-{room}",
        "sequence": sequence,
        "device_timestamp": "2026-07-04T14:00:30Z",
        "changes": [
            {
                "device_id": device_id,
                "room": room,
                "device_type": device_type,
                "status": status,
                "power_draw_w": power_draw_w,
            }
        ],
    }


def _heartbeat_payload(devices: list[dict], sequence: int = 1) -> dict:
    return {
        "message_type": "heartbeat",
        "source_id": "esp32-drawing-room",
        "sequence": sequence,
        "device_timestamp": "2026-07-04T14:00:00Z",
        "devices": devices,
    }


def test_heartbeat_updates_hot_state(phase2_client: TestClient) -> None:
    payload = _heartbeat_payload(
        [
            {
                "device_id": "drawing_room_fan_1",
                "room": "drawing_room",
                "device_type": "fan",
                "status": "on",
                "power_draw_w": 60,
            },
            {
                "device_id": "drawing_room_light_1",
                "room": "drawing_room",
                "device_type": "light",
                "status": "off",
                "power_draw_w": 15,
            },
        ]
    )
    response = phase2_client.post("/api/ingest", json=payload)

    assert response.status_code == 200
    assert set(response.json()["updated"]) == {
        "drawing_room_fan_1",
        "drawing_room_light_1",
    }

    status = phase2_client.get("/api/status").json()["data"]
    drawing_room = next(room for room in status["rooms"] if room["name"] == "Drawing Room")
    fan = next(device for device in drawing_room["devices"] if device["name"] == "Fan 1")
    assert fan["state"] == "ON"
    assert fan["wattage"] == 60
    assert drawing_room["total_wattage"] == 60


def test_unknown_device_returns_422(phase2_client: TestClient) -> None:
    payload = _state_change_payload(
        device_id="unknown_device",
        room="drawing_room",
        device_type="fan",
        status="on",
        power_draw_w=60,
    )

    response = phase2_client.post("/api/ingest", json=payload)

    assert response.status_code == 422


def test_state_change_appends_cold_log(phase2_client: TestClient) -> None:
    payload = _state_change_payload(
        device_id="work_room_1_fan_1",
        room="work_room_1",
        device_type="fan",
        status="on",
        power_draw_w=60,
    )
    phase2_client.post("/api/ingest", json=payload)

    with phase2_client.app.state.db.connection as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM state_transitions")
        assert cursor.fetchone()[0] == 1


def test_server_stamps_last_changed_on_ingest(phase2_client: TestClient) -> None:
    before = datetime.now(UTC)
    payload = _state_change_payload(
        device_id="drawing_room_light_2",
        room="drawing_room",
        device_type="light",
        status="on",
        power_draw_w=15,
    )
    phase2_client.post("/api/ingest", json=payload)
    after = datetime.now(UTC)

    record = phase2_client.app.state.hot_store.get_device("drawing_room_light_2")
    assert record is not None
    assert before <= record.last_changed <= after


def test_off_hours_alert_fires(
    phase2_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "backend.app.alerts.AlertEngine.is_office_hours",
        lambda self, now: False,
    )

    with phase2_client.websocket_connect("/ws/alerts") as websocket:
        payload = _state_change_payload(
            device_id="drawing_room_light_1",
            room="drawing_room",
            device_type="light",
            status="on",
            power_draw_w=15,
        )
        phase2_client.post("/api/ingest", json=payload)
        alert = websocket.receive_json()

    assert alert["severity"] == "warning"
    assert "outside office hours" in alert["message"]
    assert phase2_client.app.state.db.has_unresolved_alert(
        "off_hours",
        "drawing_room_light_1",
    )


def test_room_duration_alert_fires(phase2_client: TestClient) -> None:
    sequence = 1
    for entry in DEVICE_MANIFEST:
        if entry["room"] != "drawing_room":
            continue
        payload = _state_change_payload(
            device_id=entry["device_id"],
            room=entry["room"],
            device_type=entry["device_type"],
            status="on",
            power_draw_w=60 if entry["device_type"] == "fan" else 15,
            sequence=sequence,
        )
        phase2_client.post("/api/ingest", json=payload)
        sequence += 1

    assert phase2_client.app.state.db.has_unresolved_alert(
        "room_duration",
        "drawing_room",
    )


def test_alert_de_duplication(phase2_client: TestClient) -> None:
    engine = phase2_client.app.state.alert_engine
    now = datetime.now(UTC)

    for entry in DEVICE_MANIFEST:
        if entry["room"] != "work_room_2":
            continue
        record = phase2_client.app.state.hot_store.get_device(entry["device_id"])
        phase2_client.app.state.hot_store.apply_updates(
            [
                type(record)(
                    device_id=entry["device_id"],
                    room=entry["room"],
                    device_type=entry["device_type"],
                    status="on",
                    power_draw_w=60 if entry["device_type"] == "fan" else 15,
                    last_changed=now - timedelta(hours=3),
                )
            ],
            now,
        )

    asyncio.run(engine.evaluate_all(now))
    asyncio.run(engine.evaluate_all(now))

    assert (
        phase2_client.app.state.db.count_unresolved_alerts(
            "room_duration",
            "work_room_2",
        )
        == 1
    )


def test_usage_calculation_from_transitions(phase2_client: TestClient) -> None:
    now = datetime.now(UTC)
    one_hour_ago = now - timedelta(hours=1)
    record = phase2_client.app.state.hot_store.get_device("drawing_room_fan_1")
    phase2_client.app.state.hot_store.apply_updates(
        [
            type(record)(
                device_id=record.device_id,
                room=record.room,
                device_type=record.device_type,
                status="on",
                power_draw_w=1000,
                last_changed=one_hour_ago,
            )
        ],
        one_hour_ago,
    )
    phase2_client.app.state.db.log_transition(
        phase2_client.app.state.hot_store.get_device("drawing_room_fan_1"),
        one_hour_ago,
    )

    usage = phase2_client.get("/api/usage").json()["data"]
    assert usage["daily_kwh"] == pytest.approx(1.0, abs=0.05)
    drawing_room = next(
        room for room in usage["per_room"] if room["room_name"] == "Drawing Room"
    )
    assert drawing_room["kwh"] == pytest.approx(1.0, abs=0.05)


def test_dashboard_websocket_receives_diff(phase2_client: TestClient) -> None:
    with phase2_client.websocket_connect("/ws/dashboard") as websocket:
        payload = _state_change_payload(
            device_id="work_room_2_light_1",
            room="work_room_2",
            device_type="light",
            status="on",
            power_draw_w=15,
        )
        phase2_client.post("/api/ingest", json=payload)
        message = websocket.receive_json()

    assert message["message_type"] == "state_diff"
    assert message["changes"][0]["device_id"] == "work_room_2_light_1"
    assert message["total_wattage"] == 15


def test_room_lookup_accepts_slug(phase2_client: TestClient) -> None:
    response = phase2_client.get("/api/room/drawing_room")

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Drawing Room"


def test_manifest_has_fifteen_devices() -> None:
    assert len(DEVICE_MANIFEST) == 15


def test_device_duration_alert_fires_when_device_on_too_long(
    phase2_client: TestClient,
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A single device ON past DEVICE_DURATION_THRESHOLD_SECONDS fires a device_duration alert.

    With DEVICE_DURATION_THRESHOLD_SECONDS=0, any device that is ON at evaluation
    time (last_changed within microseconds of server_time) is treated as having
    crossed the boundary, since ``server_time - last_changed`` is non-negative.
    """

    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "device_duration.db"))
    monkeypatch.setenv("DEVICE_DURATION_THRESHOLD_SECONDS", "0")
    monkeypatch.setenv("DURATION_THRESHOLD_SECONDS", "999999")
    monkeypatch.setenv("ALERT_SWEEP_INTERVAL_SECONDS", "3600")
    get_settings.cache_clear()
    app = create_app()
    with TestClient(app) as client, client.websocket_connect("/ws/alerts") as websocket:
        client.post(
            "/api/ingest",
            json=_state_change_payload(
                device_id="work_room_1_light_1",
                room="work_room_1",
                device_type="light",
                status="on",
                power_draw_w=15,
            ),
        )
        alert = websocket.receive_json()

    assert alert["severity"] == "warning"
    assert "Work Room 1 Light 1" in alert["message"]
    assert app.state.db.has_unresolved_alert(
        "device_duration",
        "work_room_1_light_1",
    )
    get_settings.cache_clear()


def test_device_duration_alert_does_not_fire_within_threshold(
    phase2_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A positive threshold must gate the rule — only ON devices past the
    threshold should fire."""

    monkeypatch.setenv("DEVICE_DURATION_THRESHOLD_SECONDS", "3600")
    get_settings.cache_clear()
    try:
        engine = phase2_client.app.state.alert_engine
        # last_changed is "just now", so device is far below the 1-hour threshold.
        now = datetime.now(UTC)
        record = phase2_client.app.state.hot_store.get_device("drawing_room_fan_2")
        phase2_client.app.state.hot_store.apply_updates(
            [
                type(record)(
                    device_id=record.device_id,
                    room=record.room,
                    device_type=record.device_type,
                    status="on",
                    power_draw_w=60,
                    last_changed=now,
                )
            ],
            now,
        )
        asyncio.run(engine.evaluate_all(now))

        assert not phase2_client.app.state.db.has_unresolved_alert(
            "device_duration",
            "drawing_room_fan_2",
        )
    finally:
        get_settings.cache_clear()
