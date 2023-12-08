import ast
from typing import Any


def execute(code: str) -> Any:
    block = ast.parse(code, mode="exec")

    # assumes last node is an expression
    last = ast.Expression(block.body.pop().value)

    _globals, _locals = {}, {}
    exec(compile(block, "<string>", mode="exec"), _globals, _locals)
    return eval(compile(last, "<string>", mode="eval"), _globals, _locals)
