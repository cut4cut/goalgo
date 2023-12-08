from litestar import get, post
from litestar.controller import Controller
from litestar.di import Provide
from litestar.handlers.http_handlers.decorators import post
from litestar.pagination import OffsetPagination
from litestar.repository.filters import LimitOffset
from pydantic import TypeAdapter

from admin_service.dto.incoming import ReadDTO, WriteDTO
from admin_service.model import IncomingModel
from admin_service.repo.incoming import IncomingRepository, provide_incomings_repo


class IncomingController(Controller):
    """Incoming CRUD"""

    tags = ["Incoming"]
    dependencies = {"incomings_repo": Provide(provide_incomings_repo)}

    @get(path="/incomings")
    async def list_incomings(
        self,
        incomings_repo: IncomingRepository,
        limit_offset: LimitOffset,
    ) -> OffsetPagination[ReadDTO]:
        """List of incomings."""
        results, total = await incomings_repo.list_and_count(limit_offset)
        type_adapter = TypeAdapter(list[ReadDTO])
        return OffsetPagination[ReadDTO](
            items=type_adapter.validate_python(results),
            total=total,
            limit=limit_offset.limit,
            offset=limit_offset.offset,
        )

    @post(path="/incomings")
    async def create_incoming(
        self,
        incomings_repo: IncomingRepository,
        data: WriteDTO,
    ) -> ReadDTO:
        """Create a new incoming."""
        obj = await incomings_repo.add(
            IncomingModel(**data.model_dump(exclude_unset=True, exclude_none=True)),
        )
        await incomings_repo.session.commit()
        return ReadDTO.model_validate(obj)
