from dataclasses import asdict
from enum import Enum
from functools import wraps
from uuid import UUID

import requests
from orjson import dumps


class DataKind(str, Enum):
    ORDER = "order"
    INCOMING = "incoming"


class ApiClient:
    def __init__(self) -> None:
        self.base_url: str = "http://localhost:8000"
        self.strategy_id: UUID | None = None

    def save_incoming(self, data: dict) -> None:
        requests.post(f"{self.base_url}/incomings", data=self._serialize(data))

    def save_order(self, data: dict) -> None:
        requests.post(f"{self.base_url}/orders", data=self._serialize(data))

    def init_strategy(
        self, name: str = "Test", description: str = "Some test strategy"
    ):
        serielized = dumps(
            {"name": name, "description": description, "source_code": ""}
        )
        response = requests.post(f"{self.base_url}/strategies", data=serielized).json()
        self.strategy_id = response["id"]

    def _serialize(self, data: dict) -> str:
        return dumps({"strategy_id": self.strategy_id, "data": data})


def observeit(datakind: DataKind):
    def wrapper(func):
        @wraps(func)
        def inner_wrapper(*args, **kwds):
            result = func(*args, **kwds)

            if datakind == DataKind.INCOMING:
                if result:
                    client.save_incoming(asdict(result))
            else:
                if result:
                    client.save_order(asdict(result))
            return result

        return inner_wrapper

    return wrapper


client = ApiClient()

client.init_strategy()
