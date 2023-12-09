from uuid import UUID

from admin_service.entity import Order
from admin_service.pkg.base import BaseModel


class ReadDTO(Order):
    ...


class WriteDTO(BaseModel):
    data: dict

    strategy_id: UUID
