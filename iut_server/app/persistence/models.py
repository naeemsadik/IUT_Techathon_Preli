"""SQLite schema definitions and row types."""

from dataclasses import dataclass
from datetime import datetime

STATE_TRANSITIONS_DDL = """
CREATE TABLE IF NOT EXISTS state_transitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    room TEXT NOT NULL,
    status TEXT NOT NULL,
    power_draw_w INTEGER NOT NULL,
    recorded_at TEXT NOT NULL
);
"""

ALERT_LOG_DDL = """
CREATE TABLE IF NOT EXISTS alert_log (
    id TEXT PRIMARY KEY,
    alert_type TEXT NOT NULL,
    target TEXT NOT NULL,
    message TEXT NOT NULL,
    severity TEXT NOT NULL,
    created_at TEXT NOT NULL,
    resolved_at TEXT
);
"""

UNRESOLVED_ALERT_INDEX_DDL = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_alert_unresolved
ON alert_log(alert_type, target)
WHERE resolved_at IS NULL;
"""

TRANSITION_INDEX_DDL = """
CREATE INDEX IF NOT EXISTS idx_transitions_recorded_at
ON state_transitions(recorded_at);
"""

ALL_DDL = (
    STATE_TRANSITIONS_DDL,
    ALERT_LOG_DDL,
    UNRESOLVED_ALERT_INDEX_DDL,
    TRANSITION_INDEX_DDL,
)


@dataclass(frozen=True)
class StateTransitionRow:
    """A persisted device state transition."""

    id: int
    device_id: str
    room: str
    status: str
    power_draw_w: int
    recorded_at: datetime


@dataclass(frozen=True)
class AlertLogRow:
    """A persisted alert record."""

    id: str
    alert_type: str
    target: str
    message: str
    severity: str
    created_at: datetime
    resolved_at: datetime | None
