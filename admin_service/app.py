from litestar import Litestar
from litestar.contrib.sqlalchemy.base import UUIDBase
from litestar.contrib.sqlalchemy.plugins import (
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
    SQLAlchemyInitPlugin,
)
from litestar.di import Provide

from admin_service.controller import (
    ConfigController,
    IncomingController,
    OrderController,
    StrategyController,
)
from admin_service.pkg.provider import provide_limit_offset_pagination

session_config = AsyncSessionConfig(expire_on_commit=False)
sqlalchemy_config = SQLAlchemyAsyncConfig(
    connection_string="postgresql+asyncpg://user:pass@localhost:5432/postgres",
    session_config=session_config,
)  # Create 'db_session' dependency.
sqlalchemy_plugin = SQLAlchemyInitPlugin(config=sqlalchemy_config)


async def on_startup() -> None:
    """Initializes the database."""
    async with sqlalchemy_config.get_engine().begin() as conn:
        await conn.run_sync(UUIDBase.metadata.create_all)


app = Litestar(
    route_handlers=[
        ConfigController,
        StrategyController,
        IncomingController,
        OrderController,
    ],
    on_startup=[on_startup],
    plugins=[SQLAlchemyInitPlugin(config=sqlalchemy_config)],
    dependencies={"limit_offset": Provide(provide_limit_offset_pagination)},
    debug=True,
)
