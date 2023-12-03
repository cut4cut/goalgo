from random import randint
from typing import Any


def mocked_ctrategy(data: Any) -> bool:
    return bool(randint(0, 1))
