from uuid import UUID

from litestar.contrib.sqlalchemy.base import UUIDAuditBase
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload


class StrategyModel(UUIDAuditBase):
    __tablename__ = "strategy"

    name: Mapped[str]
    description: Mapped[str]
    source_code: Mapped[str]


class ConfigModel(UUIDAuditBase):
    __tablename__ = "config"

    comment: Mapped[str]
    is_actual: Mapped[bool]
    data: Mapped[dict]

    strategy_id: Mapped[UUID] = mapped_column(ForeignKey("strategy.id"))
    strategy: Mapped[StrategyModel] = relationship(
        lazy="joined", innerjoin=True, viewonly=True
    )


class IncomingModel(UUIDAuditBase):
    __tablename__ = "incoming"

    data: Mapped[dict]


class OrderModel(UUIDAuditBase):
    __tablename__ = "order"

    data: Mapped[dict]
