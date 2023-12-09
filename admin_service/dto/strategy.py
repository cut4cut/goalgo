from uuid import UUID

from admin_service.entity import Strategy
from admin_service.pkg.base import BaseModel


class ReadDTO(Strategy):
    ...


class WriteDTO(BaseModel):
    id: UUID | None = None
    name: str
    description: str
    source_code: str
