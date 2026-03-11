from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class JobCreate(BaseModel):
    type_id: int | None = None  # World API type ID
    blueprint_name: str
    quantity: int = 1
    assigned_to: UUID | None = None


class JobUpdate(BaseModel):
    status: str | None = None
    assigned_to: UUID | None = None
    materials_ready: bool | None = None


class JobResponse(BaseModel):
    id: UUID
    type_id: int | None
    blueprint_name: str | None
    quantity: int
    status: str
    materials_ready: bool
    assigned_to: UUID | None
    assigned_name: str | None = None
    created_by: UUID
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class InventoryItem(BaseModel):
    item_id: int  # World API type ID
    item_name: str
    quantity: int


class InventoryResponse(BaseModel):
    item_id: int
    item_name: str | None
    quantity: int
    updated_at: datetime

    model_config = {"from_attributes": True}


class MaterialGap(BaseModel):
    item_id: str
    item_name: str
    required: int
    held: int
    deficit: int


class GapAnalysisResponse(BaseModel):
    total_jobs: int
    jobs_materials_ready: int
    jobs_blocked: int
    material_gaps: list[MaterialGap]
