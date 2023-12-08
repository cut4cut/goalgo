from litestar.contrib.sqlalchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy.ext.asyncio import AsyncSession

from admin_service.model import IncomingModel


class IncomingRepository(SQLAlchemyAsyncRepository[IncomingModel]):
    """Incoming repository."""

    model_type = IncomingModel


async def provide_incomings_repo(db_session: AsyncSession) -> IncomingRepository:
    """This provides the default Incomings repository."""
    return IncomingRepository(session=db_session)
