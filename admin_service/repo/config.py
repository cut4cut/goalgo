from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.contrib.sqlalchemy.repository import SQLAlchemyAsyncRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from admin_service.model import ConfigModel


class ConfigRepository(SQLAlchemyAsyncRepository[ConfigModel]):
    """Config repository."""

    model_type = ConfigModel


async def provide_configs_repo(db_session: AsyncSession) -> ConfigRepository:
    """This provides the default Configs repository."""
    return ConfigRepository(session=db_session)
