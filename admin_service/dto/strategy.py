from admin_service.entity import Strategy
from admin_service.pkg.base import BaseModel


class ReadDTO(Strategy):
    ...


class WriteDTO(BaseModel):
    name: str
    description: str
    cource_cod: str
