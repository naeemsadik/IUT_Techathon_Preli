"""SQLite database access for cold state."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from backend.app.persistence.models import ALL_DDL, AlertLogRow, StateTransitionRow
from backend.app.state import DeviceRecord


class Database:
    """Thin wrapper around SQLite for state transitions and alert history."""

    def __init__(self, sqlite_path: str) -> None:
        self._sqlite_path = sqlite_path
        self._connection: sqlite3.Connection | None = None

    @property
    def connection(self) -> sqlite3.Connection:
        """Return an open SQLite connection, creating one if needed."""

        if self._connection is None:
            path = Path(self._sqlite_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def init_db(self) -> None:
        """Create tables and indexes if they do not exist."""

        for ddl in ALL_DDL:
            self.connection.execute(ddl)
        self.connection.commit()

    def close(self) -> None:
        """Close the underlying connection."""

        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def log_transition(self, record: DeviceRecord, recorded_at: datetime) -> None:
        """Append a state transition to the cold log."""

        self.connection.execute(
            """
            INSERT INTO state_transitions (
                device_id, room, status, power_draw_w, recorded_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                record.device_id,
                record.room,
                record.status,
                record.power_draw_w,
                recorded_at.isoformat(),
            ),
        )
        self.connection.commit()

    def query_transitions_since(self, since: datetime) -> list[StateTransitionRow]:
        """Return transitions recorded at or after the given timestamp."""

        cursor = self.connection.execute(
            """
            SELECT id, device_id, room, status, power_draw_w, recorded_at
            FROM state_transitions
            WHERE recorded_at >= ?
            ORDER BY recorded_at ASC, id ASC
            """,
            (since.isoformat(),),
        )
        return [
            StateTransitionRow(
                id=row["id"],
                device_id=row["device_id"],
                room=row["room"],
                status=row["status"],
                power_draw_w=row["power_draw_w"],
                recorded_at=datetime.fromisoformat(row["recorded_at"]),
            )
            for row in cursor.fetchall()
        ]

    def has_unresolved_alert(self, alert_type: str, target: str) -> bool:
        """Return True when an unresolved alert already exists."""

        cursor = self.connection.execute(
            """
            SELECT 1
            FROM alert_log
            WHERE alert_type = ? AND target = ? AND resolved_at IS NULL
            LIMIT 1
            """,
            (alert_type, target),
        )
        return cursor.fetchone() is not None

    def query_alerts_since(self, since: datetime) -> list[AlertLogRow]:
        """Return alerts created at or after the given timestamp."""

        cursor = self.connection.execute(
            """
            SELECT id, alert_type, target, message, severity, created_at, resolved_at
            FROM alert_log
            WHERE created_at >= ?
            ORDER BY created_at ASC
            """,
            (since.isoformat(),),
        )
        rows: list[AlertLogRow] = []
        for row in cursor.fetchall():
            rows.append(
                AlertLogRow(
                    id=row["id"],
                    alert_type=row["alert_type"],
                    target=row["target"],
                    message=row["message"],
                    severity=row["severity"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    resolved_at=(
                        datetime.fromisoformat(row["resolved_at"])
                        if row["resolved_at"]
                        else None
                    ),
                )
            )
        return rows

    def create_alert(
        self,
        alert_id: str,
        alert_type: str,
        target: str,
        message: str,
        severity: str,
        created_at: datetime,
    ) -> None:
        """Insert a new alert record."""

        self.connection.execute(
            """
            INSERT INTO alert_log (
                id, alert_type, target, message, severity, created_at, resolved_at
            ) VALUES (?, ?, ?, ?, ?, ?, NULL)
            """,
            (
                alert_id,
                alert_type,
                target,
                message,
                severity,
                created_at.isoformat(),
            ),
        )
        self.connection.commit()

    def resolve_alerts(
        self,
        alert_type: str,
        target: str,
        resolved_at: datetime,
    ) -> None:
        """Mark unresolved alerts for a type/target as resolved."""

        self.connection.execute(
            """
            UPDATE alert_log
            SET resolved_at = ?
            WHERE alert_type = ? AND target = ? AND resolved_at IS NULL
            """,
            (resolved_at.isoformat(), alert_type, target),
        )
        self.connection.commit()

    def count_unresolved_alerts(self, alert_type: str, target: str) -> int:
        """Return the number of unresolved alerts for a type/target."""

        cursor = self.connection.execute(
            """
            SELECT COUNT(*)
            FROM alert_log
            WHERE alert_type = ? AND target = ? AND resolved_at IS NULL
            """,
            (alert_type, target),
        )
        return int(cursor.fetchone()[0])
