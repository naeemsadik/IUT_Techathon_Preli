"""Simulator entry point.

Emulates 15 office devices (2 fans + 3 lights across 3 rooms) and POSTs
heartbeat and state_change payloads to the FastAPI ingestion gateway.

Run from the repo root:

    python -m simulator.simulator

Environment variables (see simulator/.env.example):
    SIMULATOR_API_URL             Backend base URL. Default: http://127.0.0.1:8000
    SIMULATOR_TOGGLE_PROB         Probability of toggling a device per room tick.
                                  Default: 0.2
    SIMULATOR_HEARTBEAT_EVERY_N   Emit a heartbeat every N ticks per room.
                                  Default: 10
    SIMULATOR_SEED                Optional integer for deterministic runs.

Optional CLI flags:
    --url URL                     Override SIMULATOR_API_URL
    --probability P               Override SIMULATOR_TOGGLE_PROB
    --room ROOM_SLUG              Run only a single room (drawing_room | work_room_1
                                  | work_room_2) — useful for debugging
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import random
import sys
from datetime import UTC, datetime
from typing import Any

import httpx


LOG = logging.getLogger("simulator")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOMS: dict[str, dict[str, Any]] = {
    "drawing_room": {
        "interval": 3,
        "source_id": "esp32-drawing-room",
        "display_name": "Drawing Room",
    },
    "work_room_1": {
        "interval": 5,
        "source_id": "esp32-work-room-1",
        "display_name": "Work Room 1",
    },
    "work_room_2": {
        "interval": 7,
        "source_id": "esp32-work-room-2",
        "display_name": "Work Room 2",
    },
}


# Per-device-type rated wattage (sent as power_draw_w regardless of status;
# backend zeros it out when status is "off" — see SYSTEM_GUIDE §4).
RATED_WATTAGE: dict[str, int] = {
    "fan": 60,
    "light": 15,
}


def build_device_manifest() -> list[dict[str, str]]:
    """Return the canonical 15-device manifest matching iut_server/app/state.py.

    2 fans + 3 lights per room across 3 rooms = 15 devices.
    """

    manifest: list[dict[str, str]] = []
    for room_slug in ROOMS:
        for fan_index in (1, 2):
            manifest.append(
                {
                    "device_id": f"{room_slug}_fan_{fan_index}",
                    "room": room_slug,
                    "device_type": "fan",
                }
            )
        for light_index in (1, 2, 3):
            manifest.append(
                {
                    "device_id": f"{room_slug}_light_{light_index}",
                    "room": room_slug,
                    "device_type": "light",
                }
            )
    return manifest


DEVICE_MANIFEST = build_device_manifest()


def env_float(name: str, default: float) -> float:
    """Parse a float env var, treating blank values as unset."""

    raw = os.getenv(name)
    return float(raw) if raw else default


def env_int(name: str, default: int | None = None) -> int | None:
    """Parse an int env var, treating blank values as unset."""

    raw = os.getenv(name)
    return int(raw) if raw else default


# ---------------------------------------------------------------------------
# Runtime state
# ---------------------------------------------------------------------------


class DeviceRuntime:
    """In-memory per-device simulator state."""

    __slots__ = ("device_id", "room", "device_type", "status", "power_draw_w")

    def __init__(self, device_id: str, room: str, device_type: str) -> None:
        self.device_id = device_id
        self.room = room
        self.device_type = device_type
        self.status = "off"
        self.power_draw_w = RATED_WATTAGE[device_type]

    def to_payload_dict(self) -> dict[str, Any]:
        """Return the JSON-serialisable representation for ingest payloads."""

        return {
            "device_id": self.device_id,
            "room": self.room,
            "device_type": self.device_type,
            "status": self.status,
            "power_draw_w": self.power_draw_w,
        }


def init_runtime() -> dict[str, DeviceRuntime]:
    """Build the runtime state, keyed by device_id."""

    runtime: dict[str, DeviceRuntime] = {}
    for entry in DEVICE_MANIFEST:
        runtime[entry["device_id"]] = DeviceRuntime(
            device_id=entry["device_id"],
            room=entry["room"],
            device_type=entry["device_type"],
        )
    return runtime


def devices_in_room(runtime: dict[str, DeviceRuntime], room_slug: str) -> list[DeviceRuntime]:
    """Return all runtime devices belonging to a room slug, sorted by id."""

    return sorted(
        (d for d in runtime.values() if d.room == room_slug),
        key=lambda d: d.device_id,
    )


# ---------------------------------------------------------------------------
# Payload construction
# ---------------------------------------------------------------------------


def now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string with Z suffix."""

    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_heartbeat(
    source_id: str,
    sequence: int,
    room_slug: str,
    runtime: dict[str, DeviceRuntime],
) -> dict[str, Any]:
    """Build a heartbeat payload covering all devices in a room."""

    return {
        "message_type": "heartbeat",
        "source_id": source_id,
        "sequence": sequence,
        "device_timestamp": now_iso(),
        "devices": [d.to_payload_dict() for d in devices_in_room(runtime, room_slug)],
    }


def build_state_change(
    source_id: str,
    sequence: int,
    device: DeviceRuntime,
) -> dict[str, Any]:
    """Build a state_change payload for a single device."""

    return {
        "message_type": "state_change",
        "source_id": source_id,
        "sequence": sequence,
        "device_timestamp": now_iso(),
        "changes": [device.to_payload_dict()],
    }


# ---------------------------------------------------------------------------
# Ingest posting
# ---------------------------------------------------------------------------


async def post_ingest(
    client: httpx.AsyncClient,
    api_base_url: str,
    payload: dict[str, Any],
) -> None:
    """POST a payload to /api/ingest. Logs and swallows non-fatal HTTP errors."""

    url = f"{api_base_url.rstrip('/')}/api/ingest"
    try:
        response = await client.post(url, json=payload, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        LOG.info(
            "POST %s seq=%d updated=%s",
            payload["message_type"],
            payload["sequence"],
            data.get("updated", []),
        )
    except httpx.HTTPStatusError as exc:
        LOG.warning(
            "HTTP %s from ingest (seq=%d): %s",
            exc.response.status_code,
            payload.get("sequence"),
            exc.response.text[:200],
        )
    except httpx.HTTPError as exc:
        LOG.warning("Network error posting ingest: %s", exc)


# ---------------------------------------------------------------------------
# Per-room loop
# ---------------------------------------------------------------------------


async def room_loop(
    client: httpx.AsyncClient,
    api_base_url: str,
    room_slug: str,
    config: dict[str, Any],
    runtime: dict[str, DeviceRuntime],
    sequences: dict[str, int],
    toggle_prob: float,
    heartbeat_every_n: int,
    rng: random.Random,
    tick_counter: dict[str, int],
) -> None:
    """Endless per-room tick loop.

    - Every N ticks, send a heartbeat (full room sync).
    - Otherwise, with probability ``toggle_prob``, pick one device in the room
      and flip it; send a targeted state_change.
    - If nothing changes, send no payload this tick.
    """

    interval = config["interval"]
    source_id = config["source_id"]

    while True:
        sequences[room_slug] += 1
        seq = sequences[room_slug]
        tick_counter[room_slug] += 1

        room_devices = devices_in_room(runtime, room_slug)
        should_heartbeat = (tick_counter[room_slug] % heartbeat_every_n) == 0

        if should_heartbeat:
            payload = build_heartbeat(source_id, seq, room_slug, runtime)
            await post_ingest(client, api_base_url, payload)
        elif rng.random() < toggle_prob and room_devices:
            target = rng.choice(room_devices)
            target.status = "on" if target.status == "off" else "off"
            payload = build_state_change(source_id, seq, target)
            await post_ingest(client, api_base_url, payload)
        # else: idle tick — emit nothing

        await asyncio.sleep(interval)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    """Parse optional CLI arguments."""

    parser = argparse.ArgumentParser(
        description="Simulate 15 office devices and POST to the FastAPI ingest gateway."
    )
    parser.add_argument(
        "--url",
        default=os.getenv("SIMULATOR_API_URL", "http://127.0.0.1:8000"),
        help="Backend base URL (default: env SIMULATOR_API_URL or http://127.0.0.1:8000)",
    )
    parser.add_argument(
        "--probability",
        type=float,
        default=env_float("SIMULATOR_TOGGLE_PROB", 0.2),
        help="Per-tick toggle probability (default: env SIMULATOR_TOGGLE_PROB or 0.2)",
    )
    parser.add_argument(
        "--room",
        choices=list(ROOMS.keys()),
        default=None,
        help="Run only a single room (debug aid). Default: all three rooms.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=env_int("SIMULATOR_SEED"),
        help="Random seed for deterministic runs (default: env SIMULATOR_SEED or non-deterministic).",
    )
    return parser.parse_args()


async def run(args: argparse.Namespace) -> None:
    """Start the simulator: initial heartbeats, then per-room loops forever."""

    api_base_url: str = args.url
    toggle_prob: float = args.probability
    heartbeat_every_n = env_int("SIMULATOR_HEARTBEAT_EVERY_N", 10) or 10
    seed: int | None = args.seed
    only_room: str | None = args.room

    if not 0.0 <= toggle_prob <= 1.0:
        raise SystemExit("--probability must be between 0 and 1")

    rng = random.Random(seed)
    runtime = init_runtime()
    sequences: dict[str, int] = {slug: 0 for slug in ROOMS}
    tick_counter: dict[str, int] = {slug: 0 for slug in ROOMS}

    selected_rooms = {only_room: ROOMS[only_room]} if only_room else ROOMS

    LOG.info("Starting simulator against %s", api_base_url)
    LOG.info(
        "Rooms: %s | toggle_prob=%.2f | heartbeat every %d ticks | seed=%s",
        ", ".join(selected_rooms.keys()),
        toggle_prob,
        heartbeat_every_n,
        seed,
    )

    async with httpx.AsyncClient() as client:
        # 1. Send initial heartbeat per room (all devices off).
        for room_slug, config in selected_rooms.items():
            sequences[room_slug] += 1
            payload = build_heartbeat(
                config["source_id"], sequences[room_slug], room_slug, runtime
            )
            await post_ingest(client, api_base_url, payload)

        LOG.info("Initial heartbeats sent. Toggling begins…")

        # 2. Start one loop per room concurrently.
        tasks = [
            asyncio.create_task(
                room_loop(
                    client=client,
                    api_base_url=api_base_url,
                    room_slug=room_slug,
                    config=config,
                    runtime=runtime,
                    sequences=sequences,
                    toggle_prob=toggle_prob,
                    heartbeat_every_n=heartbeat_every_n,
                    rng=rng,
                    tick_counter=tick_counter,
                ),
                name=f"room-loop-{room_slug}",
            )
            for room_slug, config in selected_rooms.items()
        ]

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            LOG.info("Simulator cancelled, shutting down")
            for task in tasks:
                task.cancel()
            raise


def main() -> None:
    """CLI entry point."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    args = parse_args()
    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        LOG.info("Simulator stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
