from uuid import UUID

from admin_service.entity import Config
from admin_service.pkg.base import BaseModel


class ReadDTO(Config):
    ...


class WriteDTO(BaseModel):
    comment: str
    is_actual: bool
    data: dict

    strategy_id: UUID
