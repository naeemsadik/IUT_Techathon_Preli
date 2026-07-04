"""Historical analytics endpoint.

Returns time-bucketed device state and power-draw history for the dashboard
charts. Data is computed from the SQLite `state_transitions` log.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from fastapi import APIRouter, Depends, Query

from backend.app.dependencies import get_database
from backend.app.persistence.database import Database
from shared.models import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["history"])


_RANGE_HOURS = {
    "1h": 1,
    "24h": 24,
    "7d": 24 * 7,
    "30d": 24 * 30,
}

_BUCKET_MINUTES = {
    "1h": 1,      # 1-minute buckets -> 60 points
    "24h": 60,    # 1-hour buckets -> 24 points
    "7d": 60 * 6, # 6-hour buckets -> 28 points
    "30d": 60 * 24,  # 1-day buckets -> 30 points
}


def _bucket_start(ts: datetime, bucket_minutes: int) -> datetime:
    """Round a timestamp down to the nearest bucket boundary (UTC)."""

    ts = ts.astimezone(UTC)
    discard = timedelta(
        minutes=ts.minute % bucket_minutes,
        seconds=ts.second,
        microseconds=ts.microsecond,
    )
    return (ts - discard).replace(second=0, microsecond=0)


@router.get("/history", response_model=APIResponse[dict[str, Any]])
async def get_history(
    range: Literal["1h", "24h", "7d", "30d"] = Query("24h", description="Time range"),
    database: Database = Depends(get_database),
) -> APIResponse[dict[str, Any]]:
    """Return time-bucketed power-draw history per room and per device.

    Response shape::

        {
            "range": "24h",
            "bucket_minutes": 60,
            "now": "2026-07-04T16:00:00Z",
            "since": "2026-07-03T16:00:00Z",
            "rooms": [
                {
                    "slug": "drawing_room",
                    "name": "Drawing Room",
                    "series": [
                        {"t": "2026-07-03T16:00:00Z", "watts": 75, "on_count": 3},
                        ...
                    ]
                },
                ...
            ],
            "devices": [
                {"device_id": "drawing_room_fan_1", "room": "drawing_room",
                 "device_type": "fan", "series": [...]},
                ...
            ],
            "totals": {
                "series": [{"t": "...", "watts": 75}, ...]
            },
            "alerts": [
                {"id": "...", "alert_type": "off_hours", "target": "...",
                 "message": "...", "severity": "warning",
                 "created_at": "...", "resolved_at": null},
                ...
            ]
        }
    """

    hours = _RANGE_HOURS[range]
    bucket_minutes = _BUCKET_MINUTES[range]
    now = datetime.now(UTC)
    since = now - timedelta(hours=hours)

    # --- Pull raw transitions -------------------------------------------------
    rows = database.query_transitions_since(since)

    # Build segments per device: list of (start, end, status, watts, room).
    by_device: dict[str, list[Any]] = defaultdict(list)
    for row in rows:
        by_device[row.device_id].append(row)

    # For each device, compute the "current" status from hot state fallback.
    # (If a device is currently ON and was ON before `since`, we approximate
    #  its status at `since` as "on" so the chart line starts correctly.)
    device_segments: dict[str, list[tuple[datetime, datetime, str, int, str]]] = {}
    for device_id, dev_rows in by_device.items():
        segments: list[tuple[datetime, datetime, str, int, str]] = []
        for i, row in enumerate(dev_rows):
            seg_end = dev_rows[i + 1].recorded_at if i + 1 < len(dev_rows) else now
            segments.append((row.recorded_at, seg_end, row.status, row.power_draw_w, row.room))
        device_segments[device_id] = segments

    # --- Aggregate into time buckets ------------------------------------------
    bucket_count = (hours * 60) // bucket_minutes
    # Pre-build the time axis: each bucket start (UTC) from since to now.
    bucket_starts: list[datetime] = []
    cur = _bucket_start(since, bucket_minutes)
    for _ in range(int(bucket_count) + 1):
        bucket_starts.append(cur)
        cur += timedelta(minutes=bucket_minutes)

    # room_slug -> list[buckets] of total watts and on-count
    room_buckets: dict[str, list[dict[str, Any]]] = defaultdict(
        lambda: [{"t": b.isoformat() + "Z", "watts": 0, "on_count": 0, "minutes_on": 0.0}
                 for b in bucket_starts]
    )
    device_buckets: dict[str, list[dict[str, Any]]] = {}
    for device_id in by_device:
        device_buckets[device_id] = [
            {"t": b.isoformat() + "Z", "watts": 0, "on_count": 0, "minutes_on": 0.0}
            for b in bucket_starts
        ]

    # For each device, for each segment, distribute watts across buckets.
    # We compute time-weighted wattage per bucket by clamping to bucket edges.
    for device_id, segments in device_segments.items():
        for seg_start, seg_end, status, watts, room_slug in segments:
            if status != "on" or watts <= 0:
                continue
            for i, b_start in enumerate(bucket_starts):
                b_end = b_start + timedelta(minutes=bucket_minutes)
                # Overlap between [seg_start, seg_end] and [b_start, b_end]
                ov_start = max(seg_start, b_start)
                ov_end = min(seg_end, b_end)
                if ov_end <= ov_start:
                    continue
                minutes_on = (ov_end - ov_start).total_seconds() / 60.0
                # Average watts in this bucket = watts (constant within segment)
                device_buckets[device_id][i]["watts"] += watts
                device_buckets[device_id][i]["minutes_on"] += minutes_on
                if device_buckets[device_id][i]["on_count"] == 0:
                    # device was ON at some point in this bucket
                    device_buckets[device_id][i]["on_count"] = 1
                # Aggregate into room
                rb = room_buckets[room_slug][i]
                rb["watts"] += watts
                rb["minutes_on"] += minutes_on
                if rb["on_count"] < 5:
                    rb["on_count"] += 1

    # --- Pull alert history ---------------------------------------------------
    alerts = database.query_alerts_since(since)

    # --- Compose response -----------------------------------------------------
    from backend.app.state import ROOM_SLUGS  # local import to avoid cycles

    rooms_payload: list[dict[str, Any]] = []
    for slug, display_name in ROOM_SLUGS.items():
        rooms_payload.append({
            "slug": slug,
            "name": display_name,
            "series": list(room_buckets.get(slug, [])),
        })

    devices_payload: list[dict[str, Any]] = []
    for device_id in sorted(by_device.keys()):
        # Find device type/room from any of its rows.
        first = by_device[device_id][0]
        devices_payload.append({
            "device_id": device_id,
            "room": first.room,
            "device_type": first.device_type,
            "series": device_buckets[device_id],
        })

    # Totals: sum across rooms for each bucket.
    totals_series: list[dict[str, Any]] = []
    for i in range(len(bucket_starts)):
        total_w = sum(room_buckets[s][i]["watts"] for s in ROOM_SLUGS)
        totals_series.append({"t": bucket_starts[i].isoformat() + "Z", "watts": round(total_w, 1)})

    payload = {
        "range": range,
        "bucket_minutes": bucket_minutes,
        "since": since.isoformat() + "Z",
        "now": now.isoformat() + "Z",
        "rooms": rooms_payload,
        "devices": devices_payload,
        "totals": {"series": totals_series},
        "alerts": [
            {
                "id": a.id,
                "alert_type": a.alert_type,
                "target": a.target,
                "message": a.message,
                "severity": a.severity,
                "created_at": a.created_at.isoformat() + "Z",
                "resolved_at": a.resolved_at.isoformat() + "Z" if a.resolved_at else None,
            }
            for a in alerts
        ],
    }
    return APIResponse(data=payload)