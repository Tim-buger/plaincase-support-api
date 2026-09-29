import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from app.schemas import AuditRecord, ExtractionResponse


class AuditStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS extraction_runs (
                    request_id TEXT PRIMARY KEY,
                    idempotency_key TEXT UNIQUE,
                    provider TEXT NOT NULL,
                    status TEXT NOT NULL,
                    latency_ms INTEGER NOT NULL,
                    attempts INTEGER NOT NULL,
                    response_json TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )

    def get_by_idempotency_key(self, key: str) -> ExtractionResponse | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT response_json FROM extraction_runs
                WHERE idempotency_key = ? AND status = 'ok'
                """,
                (key,),
            ).fetchone()
        if not row or not row[0]:
            return None
        return ExtractionResponse.model_validate_json(row[0])

    def save_success(self, result: ExtractionResponse, idempotency_key: str | None) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO extraction_runs
                    (request_id, idempotency_key, provider, status, latency_ms, attempts,
                     response_json, created_at)
                VALUES (?, ?, ?, 'ok', ?, ?, ?, ?)
                """,
                (
                    result.meta.request_id,
                    idempotency_key,
                    result.meta.provider,
                    result.meta.latency_ms,
                    result.meta.attempts,
                    result.model_dump_json(),
                    result.meta.created_at.isoformat(),
                ),
            )

    def save_failure(
        self, request_id: str, provider: str, attempts: int, latency_ms: int
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO extraction_runs
                    (request_id, provider, status, latency_ms, attempts, created_at)
                VALUES (?, ?, 'error', ?, ?, ?)
                """,
                (request_id, provider, latency_ms, attempts, datetime.now(UTC).isoformat()),
            )

    def recent(self, limit: int = 10) -> list[AuditRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT request_id, provider, status, latency_ms, attempts, created_at
                FROM extraction_runs ORDER BY created_at DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            AuditRecord(
                request_id=row[0],
                provider=row[1],
                status=row[2],
                latency_ms=row[3],
                attempts=row[4],
                created_at=datetime.fromisoformat(row[5]),
            )
            for row in rows
        ]

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path, timeout=5)
