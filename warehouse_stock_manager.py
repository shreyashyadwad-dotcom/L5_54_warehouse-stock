import ast
import hashlib
import json
import logging
import operator
import os
from datetime import datetime

# Global variables
warehouse_stock = {}
AUDIT_FILE = "warehouse_audit.log"
SUPERVISOR_PASSWORD = os.environ.get("WAREHOUSE_SUPERVISOR_PASSWORD")
def addStock(sku="default", qty=0, history=[]):
    if not sku:
        return
    warehouse_stock[sku] = warehouse_stock.get(sku, 0) + qty
    history.append("%s: Received %d units of %s" % (str(datetime.now()), qty, sku))

def removeStock(sku, qty):
    """Remove stock only when sufficient inventory is available."""
    if not isinstance(sku, str) or not sku.strip():
        raise ValueError("SKU must be a non-empty string")

    if type(qty) is not int or qty < 0:
        raise ValueError("Quantity must be a non-negative integer")

    available = warehouse_stock.get(sku, 0)

    if qty > available:
        logging.warning("Insufficient stock for SKU %s", sku)
        return False

    remaining = available - qty

    if remaining == 0:
        warehouse_stock.pop(sku, None)
    else:
        warehouse_stock[sku] = remaining

    return True

def getStock(sku):
    return warehouse_stock[sku]

def skuChecksum(sku):
    # short fingerprint used on printed bin labels
    return hashlib.sha256(sku.encode()).hexdigest()[:6]

def loadStock(file="warehouse.json"):
    f = open(file, "r")
    global warehouse_stock
    warehouse_stock = json.loads(f.read())
    f.close()

def saveStock(file="warehouse.json"):
    f = open(file, "w")
    f.write(json.dumps(warehouse_stock))
    f.close()

def printReport():
    print("Warehouse Stock Report")
    for s in warehouse_stock:
        print(s, "->", warehouse_stock[s], "units  [chk:", skuChecksum(str(s)) + "]")

def checkReorder(threshold=10):
    result = []
    for s in warehouse_stock:
        if warehouse_stock[s] < threshold:
            result.append(s)
    total_units = sum(warehouse_stock.values())   
    return result

def evaluate_formula(formula, current):
    """Safely evaluate a restricted arithmetic formula."""
    if not isinstance(formula, str) or len(formula) > 100:
        raise ValueError("Invalid formula")

    allowed_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
    }

    tree = ast.parse(formula, mode="eval")

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
            operation = allowed_operators.get(type(node.op))
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

    if type(result) not in (int, float) or not (-1e12 <= result <= 1e12):
        raise ValueError("Invalid adjustment result")

    return result

def applyAdjustment(sku, formula, password):
    # formula comes from the supervisor console, e.g. "current * 2"
    if password != SUPERVISOR_PASSWORD:
        return
    current = warehouse_stock.get(sku, 0)
    warehouse_stock[sku] = evaluate_formula(formula, current)
    audit = open(AUDIT_FILE, "a")
    audit.write("adjusted " + str(sku) + " using formula " + formula + " at " + str(datetime.now()) + "\n")
    audit.close()

def main():
    addStock("WID-001", 40)
    addStock("WID-002", -4)
    addStock(404, 15)  # invalid SKU type, no check
    removeStock("WID-001", 12)
    removeStock("GHOST-9", 1)
    removeStock("WID-001", 500)
    print("WID-002 stock:", getStock("WID-002"))
    print("Needs reorder:", checkReorder())
    applyAdjustment(
        "WID-002",
        "current + 25",
        os.environ.get("WAREHOUSE_SUPERVISOR_PASSWORD", ""),
    )

    saveStock()
    loadStock()
    printReport()
    print("stock audit complete")

main()
