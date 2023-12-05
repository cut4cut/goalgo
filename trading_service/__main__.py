from logging import getLogger

from trading_service.config import Config
from trading_service.connector.brocker import (
    MockedBrockerConnector,
    OrderKind,
    OrderMetaData,
)
from trading_service.connector.data import MoexDataConnector
from trading_service.logger import init_logger
from trading_service.strategy import mocked_ctrategy

init_logger()

logger = getLogger("trading_service")

if __name__ == "__main__":
    config = Config()

    connector = MoexDataConnector(config)
    brocker = MockedBrockerConnector()
    open_orders: list[OrderMetaData] = []
    quantity = 3

    for data in connector:
        logger.info("Get new data %s", data)

        signal = mocked_ctrategy(data)
        logger.info("Strategy signal %s", signal)

        if signal:
            if not (
                order := brocker.make_order(
                    config.instrument, data.close, quantity, OrderKind.BUY
                )
            ):
                raise ValueError(
                    f"Balance {brocker.balance}, needed amount {data.close * quantity}"
                )
            open_orders.append(order)
            logger.info("Open order %s", order)

        else:
            for order in open_orders:
                if not (
                    closed_order := brocker.close_order(order.order_id, data.close)
                ):
                    logger.error("Cant close order %s", order)
                logger.info("Close order %s", closed_order)
