"""Database backup and restore utilities."""
from __future__ import annotations

import gzip
import io
import json
import re
from datetime import date, datetime

from sqlalchemy import text

_DT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

from bot.database.db import SessionLocal

# Order matters — respects foreign key constraints
_TABLE_ORDER = [
    "server_configs",
    "panels",
    "appointment_types",
    "events",
    "time_slots",
    "participants",
    "time_slot_votes",
]

BACKUP_VERSION = 1


def _serialize(obj: object) -> str:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


async def create_backup() -> io.BytesIO:
    async with SessionLocal() as session:
        tables: dict[str, list[dict]] = {}
        for table in _TABLE_ORDER:
            result = await session.execute(text(f"SELECT * FROM {table}"))
            tables[table] = [dict(row) for row in result.mappings().all()]

    payload = {
        "version": BACKUP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "tables": tables,
    }

    compressed = gzip.compress(json.dumps(payload, default=_serialize).encode("utf-8"))
    buf = io.BytesIO(compressed)
    buf.seek(0)
    return buf


async def restore_backup(data: bytes) -> int:
    payload = json.loads(gzip.decompress(data).decode("utf-8"))

    if payload.get("version") != BACKUP_VERSION:
        raise ValueError(f"Unsupported backup version: {payload.get('version')}")

    tables = payload["tables"]
    total = 0

    async with SessionLocal() as session:
        # Break the circular FK (events.confirmed_slot_id → time_slots.id) before deletion
        await session.execute(text("UPDATE events SET confirmed_slot_id = NULL"))

        for table in reversed(_TABLE_ORDER):
            await session.execute(text(f"DELETE FROM {table}"))

        for table in _TABLE_ORDER:
            rows = tables.get(table, [])
            for row in rows:
                parsed = {
                    k: datetime.fromisoformat(v) if isinstance(v, str) and _DT_RE.match(v) else v
                    for k, v in row.items()
                }
                cols = ", ".join(parsed.keys())
                vals = ", ".join(f":{k}" for k in parsed.keys())
                await session.execute(
                    text(f"INSERT INTO {table} ({cols}) VALUES ({vals})"),
                    parsed,
                )
                total += 1

        await session.commit()

    return total
