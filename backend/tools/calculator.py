import ast
import operator
from collections.abc import Callable

from langchain_core.tools import tool


Number = int | float

_BINARY_OPERATORS: dict[type[ast.operator], Callable[[Number, Number], Number]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPERATORS: dict[type[ast.unaryop], Callable[[Number], Number]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _evaluate_node(node: ast.AST) -> Number:
    if isinstance(node, ast.Expression):
        return _evaluate_node(node.body)

    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value

    if isinstance(node, ast.BinOp):
        operator_fn = _BINARY_OPERATORS.get(type(node.op))
        if operator_fn is None:
            raise ValueError("Unsupported math operator.")
        left = _evaluate_node(node.left)
        right = _evaluate_node(node.right)
        return operator_fn(left, right)

    if isinstance(node, ast.UnaryOp):
        operator_fn = _UNARY_OPERATORS.get(type(node.op))
        if operator_fn is None:
            raise ValueError("Unsupported unary operator.")
        return operator_fn(_evaluate_node(node.operand))

    raise ValueError("Only basic arithmetic expressions are supported.")


def safe_calculate(expression: str) -> Number:
    expression = expression.strip()
    if not expression:
        raise ValueError("Expression is empty.")
    if len(expression) > 120:
        raise ValueError("Expression is too long.")

    parsed = ast.parse(expression, mode="eval")
    result = _evaluate_node(parsed)
    if abs(result) > 1_000_000_000_000:
        raise ValueError("Result is outside the allowed range.")
    return result


@tool("calculator")
def calculator(expression: str) -> str:
    """Evaluate a basic arithmetic expression with +, -, *, /, //, %, and **."""
    try:
        return str(safe_calculate(expression))
    except Exception as exc:
        return f"Calculator error: {exc}"
