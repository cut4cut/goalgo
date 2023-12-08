from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from logging import getLogger
from typing import Annotated, Protocol
from uuid import UUID, uuid4

from annotated_types import Ge

from trading_service.utils import now_dt_mostz

logger = getLogger("brocker_connector")

NonNegative = Annotated[float, Ge(0)]


class OrderKind(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    PROCCESSING = "processing"
    OPEN = "open"
    CANCELLED = "cancelled"
    CLOSE = "close"


@dataclass
class OrderMetaData:
    order_id: UUID
    instrument: str
    kind: OrderKind
    status: OrderStatus

    open_price: NonNegative
    close_price: NonNegative | None
    quantity: NonNegative

    open_dt: datetime
    close_dt: datetime | None


class BrockerConnector(Protocol):
    def make_order(
        self,
        instrument: str,
        price: NonNegative,
        quantity: NonNegative,
        kind: OrderKind,
    ) -> OrderMetaData | None:
        ...

    def close_order(self, order_id: UUID, price: NonNegative) -> OrderMetaData | None:
        ...


class MockedBrockerConnector:
    def __init__(self):
        self.balance: float = 50_000.0
        self.orders: dict[UUID, OrderMetaData] = {}

    def make_order(
        self,
        instrument: str,
        price: NonNegative,
        quantity: NonNegative,
        kind: OrderKind,
    ) -> OrderMetaData | None:
        if (amount := price * quantity) > self.balance or self.balance <= 0:
            return None
        self.balance -= amount

        new_order = OrderMetaData(
            order_id=uuid4(),
            instrument=instrument,
            kind=kind,
            status=OrderStatus.OPEN,
            open_price=price,
            close_price=None,
            quantity=quantity,
            open_dt=now_dt_mostz(),
            close_dt=None,
        )
        self.orders[new_order.order_id] = new_order

        return new_order

    def close_order(self, order_id: UUID, price: NonNegative) -> OrderMetaData | None:
        if not (order := self.orders.get(order_id, None)):
            return None

        order.status = OrderStatus.CLOSE
        order.close_price = price
        order.close_dt = now_dt_mostz()

        profit = self._calc_profit(order)
        self.balance += profit

        del self.orders[order_id]
        return order

    @staticmethod
    def _calc_profit(order: OrderMetaData) -> float:
        assert order.close_price is not None
        ratio = 1 if order.kind == OrderKind.BUY else -1
        return (
            ratio * (float(order.close_price) - order.open_price) * order.quantity
            + order.open_price * order.quantity
        )
