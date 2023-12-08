from litestar.contrib.sqlalchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy.ext.asyncio import AsyncSession

from admin_service.model import OrderModel


class OrderRepository(SQLAlchemyAsyncRepository[OrderModel]):
    """Order repository."""

    model_type = OrderModel


async def provide_orders_repo(db_session: AsyncSession) -> OrderRepository:
    """This provides the default Incomings repository."""
    return OrderRepository(session=db_session)
