from datetime import datetime
from uuid import UUID

from pydantic.dataclasses import dataclass

from admin_service.pkg.base import BaseModel


class Config(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime

    comment: str
    is_actual: bool
    data: dict

    strategy_id: UUID


class Strategy(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime

    name: str
    description: str
    source_code: str


class Incoming(BaseModel):
    id: UUID
    created: datetime
    data: dict

    strategy_id: UUID


class Order(BaseModel):
    id: UUID
    created: datetime
    data: dict

    strategy_id: UUID
