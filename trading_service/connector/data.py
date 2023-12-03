from datetime import MINYEAR, datetime
from logging import getLogger
from time import sleep
from typing import Any, Generator, Protocol

from moexalgo import Ticker
from moexalgo.models import Candle

from trading_service.config import Config
from trading_service.utils import nowday_mostz

logger = getLogger("data_connector")


class DataConnector(Protocol):
    def __init__(self, config: Config):
        ...

    def __iter__(self) -> Generator[Candle, Any, None]:
        ...


class MoexDataConnector:
    def __init__(self, config: Config):
        self._ticker = Ticker(config.instrument)
        # TODO: Add support for periods not in minutes
        self._period = config.period
        self._last_candle_td = datetime(MINYEAR, 1, 1)

    def __iter__(self) -> Generator[Candle, Any, None]:
        while True:
            for candle in self._ticker.candles(
                date=nowday_mostz(), period=self._period
            ):
                if self._last_candle_td < candle.end:
                    yield candle
                    self._last_candle_td = candle.end
                else:
                    logger.warn(
                        "Duplicated candle with timedelta=%s", self._last_candle_td
                    )
            # May be need to check data more often than the period
            sleep(self._period * 60)
