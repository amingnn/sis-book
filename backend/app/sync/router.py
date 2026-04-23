from fastapi import APIRouter, HTTPException

from app.sync.models import SyncRunPayload, SyncSettingsPayload
from app.sync.service import (
    SyncError,
    choose_sync_dir,
    get_status,
    run_sync,
    save_settings,
)

router = APIRouter(prefix="/api/sync", tags=["数据同步"])


def _raise_sync_error(exc: SyncError):
    raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/status")
def read_status():
    try:
        return get_status()
    except SyncError as exc:
        _raise_sync_error(exc)


@router.put("/settings")
def update_settings(payload: SyncSettingsPayload):
    try:
        return save_settings(
            sync_base_dir=payload.sync_base_dir,
            enabled=payload.enabled,
            interval_minutes=payload.interval_minutes,
        )
    except SyncError as exc:
        _raise_sync_error(exc)


@router.post("/browse")
def browse_sync_dir():
    try:
        return {"path": choose_sync_dir()}
    except SyncError as exc:
        _raise_sync_error(exc)


@router.post("/run")
def run_sync_now(payload: SyncRunPayload):
    try:
        return run_sync(force_direction=payload.force_direction.strip() or None)
    except SyncError as exc:
        _raise_sync_error(exc)
