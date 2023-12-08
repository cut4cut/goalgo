from litestar.contrib.sqlalchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy.ext.asyncio import AsyncSession

from admin_service.model import StrategyModel


class StrategyRepository(SQLAlchemyAsyncRepository[StrategyModel]):
    """Strategy repository."""

    model_type = StrategyModel


async def provide_strategys_repo(db_session: AsyncSession) -> StrategyRepository:
    """This provides the default Strategys repository."""
    return StrategyRepository(session=db_session)
