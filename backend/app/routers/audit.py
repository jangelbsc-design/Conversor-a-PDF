"""Router de audit log."""
from fastapi import APIRouter, Query
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.utils.event_log import read_events

router = APIRouter()


@router.get("/")
async def get_audit_log(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """
    Retorna entradas del log de auditoría append-only.
    Lee del archivo JSONL en disco (store/audit.jsonl).
    Eventos ordenados de más reciente a más antiguo.
    """
    events = read_events(limit=limit, offset=offset)
    return {
        "events": events,
        "count": len(events),
        "offset": offset,
        "limit": limit,
    }
