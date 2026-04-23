from pydantic import BaseModel, Field


class SyncSettingsPayload(BaseModel):
    sync_base_dir: str = ""
    enabled: bool = False
    interval_minutes: int = Field(default=30, ge=5, le=1440)


class SyncRunPayload(BaseModel):
    force_direction: str = ""
