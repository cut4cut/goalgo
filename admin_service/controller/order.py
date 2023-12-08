from litestar import get, post
from litestar.controller import Controller
from litestar.di import Provide
from litestar.handlers.http_handlers.decorators import post
from litestar.pagination import OffsetPagination
from litestar.repository.filters import LimitOffset
from pydantic import TypeAdapter

from admin_service.dto.order import ReadDTO, WriteDTO
from admin_service.model import OrderModel
from admin_service.repo.order import OrderRepository, provide_orders_repo


class OrderController(Controller):
    """Order CRUD"""

    tags = ["Order"]
    dependencies = {"orders_repo": Provide(provide_orders_repo)}

    @get(path="/orders")
    async def list_orders(
        self,
        orders_repo: OrderRepository,
        limit_offset: LimitOffset,
    ) -> OffsetPagination[ReadDTO]:
        """List of orders."""
        results, total = await orders_repo.list_and_count(limit_offset)
        type_adapter = TypeAdapter(list[ReadDTO])
        return OffsetPagination[ReadDTO](
            items=type_adapter.validate_python(results),
            total=total,
            limit=limit_offset.limit,
            offset=limit_offset.offset,
        )

    @post(path="/orders")
    async def create_order(
        self,
        orders_repo: OrderRepository,
        data: WriteDTO,
    ) -> ReadDTO:
        """Create a new order."""
        obj = await orders_repo.add(
            OrderModel(**data.model_dump(exclude_unset=True, exclude_none=True)),
        )
        await orders_repo.session.commit()
        return ReadDTO.model_validate(obj)
