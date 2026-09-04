"""Small append-only JSON audit store used by graph nodes and the UI."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from models import AuditEntry


DEFAULT_AUDIT_PATH = Path(__file__).with_name("audit_log.json")


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


class AuditStore:
    def __init__(self, path: str | Path = DEFAULT_AUDIT_PATH) -> None:
        self.path = Path(path)

    def read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise RuntimeError(f"Cannot read audit log {self.path}: {exc}") from exc
        if not isinstance(value, list):
            raise RuntimeError("Audit log must contain a JSON list")
        return value

    def append(self, entry: AuditEntry) -> None:
        records = self.read()
        records.append(entry.model_dump(mode="json"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_name(f"{self.path.name}.tmp")
        temporary_path.write_text(
            json.dumps(records, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary_path, self.path)


def append_audit(store: AuditStore, **fields: Any) -> AuditEntry:
    entry = AuditEntry(**fields)
    store.append(entry)
    return entry


def load_audit_records(path: str | Path = DEFAULT_AUDIT_PATH) -> list[dict[str, Any]]:
    return AuditStore(path).read()
