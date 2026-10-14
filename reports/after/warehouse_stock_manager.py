
"""Manage warehouse stock, inventory reports, and supervisor adjustments."""

import ast
import hashlib
import json
import logging
import math
import operator
import os
from datetime import datetime

warehouse_stock = {}
AUDIT_FILE = "warehouse_audit.log"
STOCK_FILE = "warehouse.json"
PASSWORD_ENV = "WAREHOUSE_" + "SUPERVISOR_PASSWORD"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


def add_stock(sku="default", qty=0, history=None):
    """Add a non-negative quantity to a valid SKU."""
    if not isinstance(sku, str) or not sku.strip():
        raise ValueError("SKU must be a non-empty string")
    if not isinstance(qty, int) or isinstance(qty, bool) or qty < 0:
        raise ValueError("Quantity must be a non-negative integer")

    if history is None:
        history = []

    warehouse_stock[sku] = warehouse_stock.get(sku, 0) + qty
    history.append(
        f"{datetime.now()}: Received {qty} units of {sku}"
    )


def remove_stock(sku, qty):
    """Remove stock only when sufficient inventory is available."""
    if not isinstance(sku, str) or not sku.strip():
        raise ValueError("SKU must be a non-empty string")
    if not isinstance(qty, int) or isinstance(qty, bool) or qty < 0:
        raise ValueError("Quantity must be a non-negative integer")

    available = warehouse_stock.get(sku, 0)
    if qty > available:
        logger.warning("Insufficient stock for SKU %s", sku)
        return False

    remaining = available - qty
    if remaining == 0:
        warehouse_stock.pop(sku, None)
    else:
        warehouse_stock[sku] = remaining
    return True


def get_stock(sku):
    """Return the stock quantity for a SKU, or zero if absent."""
    return warehouse_stock.get(sku, 0)


def sku_checksum(sku):
    """Return a short, non-security fingerprint for a bin label."""
    return hashlib.sha256(str(sku).encode("utf-8")).hexdigest()[:6]


def load_stock(file=STOCK_FILE):
    """Load and validate inventory data from a JSON file."""
    with open(file, "r", encoding="utf-8") as stock_file:
        data = json.load(stock_file)

    if not isinstance(data, dict):
        raise ValueError("Stock file must contain a JSON object")

    for sku, qty in data.items():
        if (
            not isinstance(sku, str)
            or not isinstance(qty, int)
            or isinstance(qty, bool)
            or qty < 0
        ):
            raise ValueError("Invalid stock entry")

    warehouse_stock.clear()
    warehouse_stock.update(data)


def save_stock(file=STOCK_FILE):
    """Save the current inventory to a JSON file."""
    with open(file, "w", encoding="utf-8") as stock_file:
        json.dump(warehouse_stock, stock_file, indent=2)


def print_report():
    """Print each SKU, its quantity, and its label fingerprint."""
    print("Warehouse Stock Report")
    for sku, qty in warehouse_stock.items():
        print(
            f"{sku} -> {qty} units "
            f"[chk: {sku_checksum(sku)}]"
        )


def check_reorder(threshold=10):
    """Return SKUs whose quantities are below the reorder threshold."""
    if not isinstance(threshold, int) or threshold < 0:
        raise ValueError("Threshold must be a non-negative integer")

    return [
        sku
        for sku, qty in warehouse_stock.items()
        if qty < threshold
    ]


def evaluate_formula(formula, current):
    """Evaluate restricted arithmetic involving the current stock."""
    if not isinstance(formula, str) or len(formula) > 100:
        raise ValueError("Invalid formula")

    try:
        tree = ast.parse(formula, mode="eval")
    except SyntaxError as exc:
        raise ValueError("Invalid formula syntax") from exc

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)

        if isinstance(node, ast.Constant):
            if type(node.value) not in (int, float):
                raise ValueError("Only numeric constants are allowed")
            return node.value

        if isinstance(node, ast.Name) and node.id == "current":
            return current

        if isinstance(node, ast.BinOp):
            operation = ALLOWED_OPERATORS.get(type(node.op))
            if operation is None:
                raise ValueError("Unsupported operator")
            return operation(evaluate(node.left), evaluate(node.right))

        if isinstance(node, ast.UnaryOp) and isinstance(
            node.op, (ast.UAdd, ast.USub)
        ):
            value = evaluate(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value

        raise ValueError("Invalid adjustment formula")

    result = evaluate(tree)
    if (
        type(result) not in (int, float)
        or not math.isfinite(result)
        or not 0 <= result <= 1e12
    ):
        raise ValueError("Invalid adjustment result")

    return result


def apply_adjustment(sku, formula, password):
    """Apply a validated stock adjustment after supervisor authentication."""
    expected_password = os.environ.get(PASSWORD_ENV)
    if not expected_password or password != expected_password:
        logger.warning("Unauthorized stock adjustment attempt")
        return False

    current = warehouse_stock.get(sku, 0)
    adjusted = evaluate_formula(formula, current)

    if not isinstance(adjusted, int):
        if not adjusted.is_integer():
            raise ValueError("Stock quantity must be a whole number")
        adjusted = int(adjusted)

    with open(AUDIT_FILE, "a", encoding="utf-8") as audit:
        audit.write(
            f"Adjusted {sku} from {current} to {adjusted} "
            f"at {datetime.now().isoformat()}\n"
        )

    warehouse_stock[sku] = adjusted
    return True


def main():
    """Run a demonstration of common warehouse stock operations."""
    add_stock("WID-001", 40)
    add_stock("WID-002", 4)
    add_stock("WID-003", 15)

    remove_stock("WID-001", 12)
    remove_stock("GHOST-9", 1)
    remove_stock("WID-001", 500)

    print("WID-002 stock:", get_stock("WID-002"))
    print("Needs reorder:", check_reorder())

    password = os.environ.get(PASSWORD_ENV, "")
    if apply_adjustment("WID-002", "current + 25", password):
        print("Stock adjustment completed")

    save_stock()
    load_stock()
    print_report()
    print("Stock audit complete")


if __name__ == "__main__":
    main()
