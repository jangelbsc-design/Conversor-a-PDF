"""
Event log append-only en JSONL.
Cada línea es un JSON con timestamp, evento y hashes.
NUNCA se modifica ni borra — solo se añaden líneas al final.
"""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import settings


def append_event(
    event_type: str,
    doc_id: str | None = None,
    operation_id: str | None = None,
    details: dict[str, Any] | None = None,
    sha256_before: str | None = None,
    sha256_after: str | None = None,
    actor: str = "local_user",
    ip_address: str | None = None,
) -> dict:
    """
    Añade un evento al log JSONL append-only en disco.
    Retorna el evento registrado.
    """
    event = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "doc_id": doc_id,
        "operation_id": operation_id,
        "details": details or {},
        "sha256_before": sha256_before,
        "sha256_after": sha256_after,
        "actor": actor,
        "ip_address": ip_address,
    }

    log_path = settings.audit_log_path
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Modo 'a' (append) — nunca trunca ni sobreescribe
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    return event


def read_events(limit: int = 200, offset: int = 0) -> list[dict]:
    """Lee eventos del log JSONL (para la UI de auditoría)."""
    log_path = settings.audit_log_path
    if not log_path.exists():
        return []

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    # Últimos eventos primero
    lines = lines[::-1]
    selected = lines[offset : offset + limit]
    return [json.loads(line) for line in selected]
