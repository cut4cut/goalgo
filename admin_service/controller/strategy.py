from litestar import get, post
from litestar.controller import Controller
from litestar.di import Provide
from litestar.handlers.http_handlers.decorators import post
from litestar.pagination import OffsetPagination
from litestar.repository.filters import LimitOffset
from pydantic import TypeAdapter

from admin_service.dto.strategy import ReadDTO, WriteDTO
from admin_service.model import StrategyModel
from admin_service.repo.strategy import StrategyRepository, provide_strategys_repo


class StrategyController(Controller):
    """Strategy CRUD"""

    tags = ["Strategy"]
    dependencies = {"strategys_repo": Provide(provide_strategys_repo)}

    @get(path="/strategies")
    async def list_strategys(
        self,
        strategys_repo: StrategyRepository,
        limit_offset: LimitOffset,
    ) -> OffsetPagination[ReadDTO]:
        """List of strategys."""
        results, total = await strategys_repo.list_and_count(limit_offset)
        type_adapter = TypeAdapter(list[ReadDTO])
        return OffsetPagination[ReadDTO](
            items=type_adapter.validate_python(results),
            total=total,
            limit=limit_offset.limit,
            offset=limit_offset.offset,
        )

    @post(path="/strategies")
    async def create_strategy(
        self,
        strategys_repo: StrategyRepository,
        data: WriteDTO,
    ) -> ReadDTO:
        """Create a new strategy."""
        obj = await strategys_repo.add(
            StrategyModel(**data.model_dump(exclude_unset=True, exclude_none=True)),
        )
        await strategys_repo.session.commit()
        return ReadDTO.model_validate(obj)
