from uuid import UUID

from admin_service.entity import Incoming
from admin_service.pkg.base import BaseModel


class ReadDTO(Incoming):
    ...


class WriteDTO(BaseModel):
    data: dict

    strategy_id: UUID
