from litestar import get
from litestar.controller import Controller
from litestar.di import Provide
from litestar.handlers.http_handlers.decorators import post
from litestar.pagination import OffsetPagination
from litestar.repository.filters import LimitOffset
from pydantic import TypeAdapter

from admin_service.dto.config import ReadDTO, WriteDTO
from admin_service.model import ConfigModel
from admin_service.repo.config import ConfigRepository, provide_configs_repo


class ConfigController(Controller):
    """Config CRUD"""

    tags = ["Config"]
    dependencies = {"configs_repo": Provide(provide_configs_repo)}

    @get(path="/configs")
    async def list_configs(
        self,
        configs_repo: ConfigRepository,
        limit_offset: LimitOffset,
    ) -> OffsetPagination[ReadDTO]:
        """List of configs."""
        results, total = await configs_repo.list_and_count(limit_offset)
        type_adapter = TypeAdapter(list[ReadDTO])
        return OffsetPagination[ReadDTO](
            items=type_adapter.validate_python(results),
            total=total,
            limit=limit_offset.limit,
            offset=limit_offset.offset,
        )

    @post(path="/configs")
    async def create_config(
        self,
        configs_repo: ConfigRepository,
        data: WriteDTO,
    ) -> ReadDTO:
        """Create a new config."""
        obj = await configs_repo.add(
            ConfigModel(**data.model_dump(exclude_unset=True, exclude_none=True)),
        )
        await configs_repo.session.commit()
        return ReadDTO.model_validate(obj)
