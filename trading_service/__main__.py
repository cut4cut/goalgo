from logging import getLogger
from uuid import UUID

from trading_service.config import Config
from trading_service.connector.brocker import MockedBrockerConnector, OrderKind
from trading_service.connector.data import MoexDataConnector
from trading_service.strategy import mocked_ctrategy

logger = getLogger("trading_service")

if __name__ == "__main__":
    config = Config()

    connector = MoexDataConnector(config)
    brocker = MockedBrockerConnector()
    open_orders: list[UUID] = []
    quantity = 3

    for data in connector:
        logger.info("Get new data %s", data)

        if mocked_ctrategy(data):
            if not (
                order := brocker.make_order(
                    config.instrument, data.close, quantity, OrderKind.BUY
                )
            ):
                raise ValueError(
                    f"Balance {brocker.balance}, needed amount {data.close * quantity}"
                )
            open_orders.append(order.order_id)
            logger.info("Make new order %s", order)

        else:
            for order_id in open_orders:
                if not (order := brocker.close_order(order_id, data.close)):
                    raise ValueError
                logger.info("Close order %s", order)
