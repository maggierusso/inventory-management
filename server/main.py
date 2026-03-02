from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import json
import os
import uuid
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders

app = FastAPI(title="Factory Inventory Management System")

# Quarter mapping for date filtering
QUARTER_MAP = {
    'Q1-2025': ['2025-01', '2025-02', '2025-03'],
    'Q2-2025': ['2025-04', '2025-05', '2025-06'],
    'Q3-2025': ['2025-07', '2025-08', '2025-09'],
    'Q4-2025': ['2025-10', '2025-11', '2025-12']
}

def filter_by_month(items: list, month: Optional[str]) -> list:
    """Filter items by month/quarter based on order_date field"""
    if not month or month == 'all':
        return items

    if month.startswith('Q'):
        # Handle quarters
        if month in QUARTER_MAP:
            months = QUARTER_MAP[month]
            return [item for item in items if any(m in item.get('order_date', '') for m in months)]
    else:
        # Direct month match
        return [item for item in items if month in item.get('order_date', '')]

    return items

def apply_filters(items: list, warehouse: Optional[str] = None, category: Optional[str] = None,
                 status: Optional[str] = None) -> list:
    """Apply common filters to a list of items"""
    filtered = items

    if warehouse and warehouse != 'all':
        filtered = [item for item in filtered if item.get('warehouse') == warehouse]

    if category and category != 'all':
        filtered = [item for item in filtered if item.get('category', '').lower() == category.lower()]

    if status and status != 'all':
        filtered = [item for item in filtered if item.get('status', '').lower() == status.lower()]

    return filtered

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class InventoryItem(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    warehouse: str
    quantity_on_hand: int
    reorder_point: int
    unit_cost: float
    location: str
    last_updated: str

class Order(BaseModel):
    id: str
    order_number: str
    customer: str
    items: List[dict]
    status: str
    order_date: str
    expected_delivery: str
    total_value: float
    actual_delivery: Optional[str] = None
    warehouse: Optional[str] = None
    category: Optional[str] = None

class DemandForecast(BaseModel):
    id: str
    item_sku: str
    item_name: str
    current_demand: int
    forecasted_demand: int
    trend: str
    period: str

class BacklogItem(BaseModel):
    id: str
    order_id: str
    item_sku: str
    item_name: str
    quantity_needed: int
    quantity_available: int
    days_delayed: int
    priority: str
    has_purchase_order: Optional[bool] = False

class PurchaseOrder(BaseModel):
    id: str
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    status: str
    created_date: str
    notes: Optional[str] = None

class CreatePurchaseOrderRequest(BaseModel):
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    notes: Optional[str] = None

# API endpoints
@app.get("/")
def root():
    return {"message": "Factory Inventory Management System API", "version": "1.0.0"}

@app.get("/api/inventory", response_model=List[InventoryItem])
def get_inventory(
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """Get all inventory items with optional filtering"""
    return apply_filters(inventory_items, warehouse, category)

@app.get("/api/inventory/{item_id}", response_model=InventoryItem)
def get_inventory_item(item_id: str):
    """Get a specific inventory item"""
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.get("/api/orders", response_model=List[Order])
def get_orders(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get all orders with optional filtering"""
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)
    return filtered_orders

@app.get("/api/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    """Get a specific order"""
    order = next((order for order in orders if order["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/api/demand", response_model=List[DemandForecast])
def get_demand_forecasts():
    """Get demand forecasts"""
    return demand_forecasts

@app.get("/api/backlog", response_model=List[BacklogItem])
def get_backlog():
    """Get backlog items with purchase order status"""
    # Add has_purchase_order flag to each backlog item
    result = []
    for item in backlog_items:
        item_dict = dict(item)
        # Check if this backlog item has a purchase order
        has_po = any(po["backlog_item_id"] == item["id"] for po in purchase_orders)
        item_dict["has_purchase_order"] = has_po
        result.append(item_dict)
    return result

@app.get("/api/dashboard/summary")
def get_dashboard_summary(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get summary statistics for dashboard with optional filtering"""
    # Filter inventory
    filtered_inventory = apply_filters(inventory_items, warehouse, category)

    # Filter orders
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)

    total_inventory_value = sum(item["quantity_on_hand"] * item["unit_cost"] for item in filtered_inventory)
    low_stock_items = len([item for item in filtered_inventory if item["quantity_on_hand"] <= item["reorder_point"]])
    pending_orders = len([order for order in filtered_orders if order["status"] in ["Processing", "Backordered"]])
    total_backlog_items = len(backlog_items)

    return {
        "total_inventory_value": round(total_inventory_value, 2),
        "low_stock_items": low_stock_items,
        "pending_orders": pending_orders,
        "total_backlog_items": total_backlog_items,
        "total_orders_value": sum(order["total_value"] for order in filtered_orders)
    }

@app.get("/api/spending/summary")
def get_spending_summary():
    """Get spending summary statistics"""
    return spending_summary

@app.get("/api/spending/monthly")
def get_monthly_spending():
    """Get monthly spending breakdown"""
    return monthly_spending

@app.get("/api/spending/categories")
def get_category_spending():
    """Get spending by category"""
    return category_spending

@app.get("/api/spending/transactions")
def get_recent_transactions():
    """Get recent transactions"""
    return recent_transactions

@app.get("/api/reports/quarterly")
def get_quarterly_reports():
    """Get quarterly performance reports"""
    # Calculate quarterly statistics from orders
    quarters = {}

    for order in orders:
        order_date = order.get('order_date', '')
        # Determine quarter
        if '2025-01' in order_date or '2025-02' in order_date or '2025-03' in order_date:
            quarter = 'Q1-2025'
        elif '2025-04' in order_date or '2025-05' in order_date or '2025-06' in order_date:
            quarter = 'Q2-2025'
        elif '2025-07' in order_date or '2025-08' in order_date or '2025-09' in order_date:
            quarter = 'Q3-2025'
        elif '2025-10' in order_date or '2025-11' in order_date or '2025-12' in order_date:
            quarter = 'Q4-2025'
        else:
            continue

        if quarter not in quarters:
            quarters[quarter] = {
                'quarter': quarter,
                'total_orders': 0,
                'total_revenue': 0,
                'delivered_orders': 0,
                'avg_order_value': 0
            }

        quarters[quarter]['total_orders'] += 1
        quarters[quarter]['total_revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            quarters[quarter]['delivered_orders'] += 1

    # Calculate averages and fulfillment rate
    result = []
    for q, data in quarters.items():
        if data['total_orders'] > 0:
            data['avg_order_value'] = round(data['total_revenue'] / data['total_orders'], 2)
            data['fulfillment_rate'] = round((data['delivered_orders'] / data['total_orders']) * 100, 1)
        result.append(data)

    # Sort by quarter
    result.sort(key=lambda x: x['quarter'])
    return result

@app.get("/api/reports/monthly-trends")
def get_monthly_trends():
    """Get month-over-month trends"""
    months = {}

    for order in orders:
        order_date = order.get('order_date', '')
        if not order_date:
            continue

        # Extract month (format: YYYY-MM-DD)
        month = order_date[:7]  # Gets YYYY-MM

        if month not in months:
            months[month] = {
                'month': month,
                'order_count': 0,
                'revenue': 0,
                'delivered_count': 0
            }

        months[month]['order_count'] += 1
        months[month]['revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            months[month]['delivered_count'] += 1

    # Convert to list and sort
    result = list(months.values())
    result.sort(key=lambda x: x['month'])
    return result


# --------------------------------------------------------------------------
# Restocking
# --------------------------------------------------------------------------

RESTOCK_ORDERS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'restock_orders.json')

# Unit cost + category lookup for demand-forecast SKUs.
# The demand_forecasts.json dataset is disjoint from inventory.json, so we
# can't join on SKU to get cost/category — we mock realistic values here.
DEMAND_ITEM_META = {
    'WDG-001': {'unit_cost': 12.50, 'category': 'Actuators'},
    'BRG-102': {'unit_cost': 8.75,  'category': 'Actuators'},
    'GSK-203': {'unit_cost': 3.20,  'category': 'Sensors'},
    'MTR-304': {'unit_cost': 145.00,'category': 'Actuators'},
    'FLT-405': {'unit_cost': 6.40,  'category': 'Sensors'},
    'VLV-506': {'unit_cost': 22.00, 'category': 'Actuators'},
    'PSU-501': {'unit_cost': 34.99, 'category': 'Power Supplies'},
    'SNR-420': {'unit_cost': 11.25, 'category': 'Sensors'},
    'CTL-330': {'unit_cost': 89.00, 'category': 'Controllers'},
}

# Lead time in days, keyed by category. Used to compute expected_delivery
# when a restock order is submitted.
CATEGORY_LEAD_TIME_DAYS = {
    'Circuit Boards': 10,
    'Sensors': 7,
    'Actuators': 14,
    'Controllers': 12,
    'Power Supplies': 9,
}
DEFAULT_LEAD_TIME_DAYS = 10

# Trend priority: increasing items are filled first, then stable, then decreasing.
# Lower value = higher priority (used as primary sort key).
TREND_PRIORITY = {'increasing': 0, 'stable': 1, 'decreasing': 2}


class RestockRecommendation(BaseModel):
    sku: str
    name: str
    category: str
    trend: str
    unit_cost: float
    quantity: int
    line_total: float
    lead_time_days: int


class RestockOrderItem(BaseModel):
    sku: str
    name: str
    category: str
    quantity: int
    unit_cost: float
    line_total: float
    lead_time_days: int


class RestockOrder(BaseModel):
    id: str
    submitted_at: str
    total_cost: float
    budget: float
    items: List[RestockOrderItem]
    expected_delivery: str
    max_lead_time_days: int


class SubmitRestockRequest(BaseModel):
    budget: float
    items: List[RestockOrderItem]


def _load_restock_orders() -> list:
    with open(RESTOCK_ORDERS_PATH, 'r') as f:
        return json.load(f)


def _save_restock_orders(data: list) -> None:
    with open(RESTOCK_ORDERS_PATH, 'w') as f:
        json.dump(data, f, indent=2)


@app.get("/api/restock/recommendations")
def get_restock_recommendations(budget: float = 10000.0):
    """Recommend which items to restock given a budget.

    Priority: increasing-trend items first, then stable, then decreasing.
    Within each tier, cheaper unit_cost wins so coverage is maximized.
    Each item is filled up to (forecasted_demand - current_demand) or
    however many units the remaining budget allows.
    """
    candidates = []
    for forecast in demand_forecasts:
        sku = forecast['item_sku']
        meta = DEMAND_ITEM_META.get(sku)
        # Skip items we have no cost/category metadata for — can't price them.
        if not meta:
            continue

        # Only recommend items where demand is expected to grow or hold.
        # We still include decreasing-trend items but they sort last and
        # usually won't fit in a constrained budget.
        shortfall = max(0, forecast['forecasted_demand'] - forecast['current_demand'])
        if shortfall == 0:
            continue

        candidates.append({
            'sku': sku,
            'name': forecast['item_name'],
            'trend': forecast['trend'],
            'unit_cost': meta['unit_cost'],
            'category': meta['category'],
            'shortfall': shortfall,
        })

    # Sort by (trend priority, unit_cost) — greedy fill favors cheap,
    # high-urgency items so a small budget still covers the important stuff.
    candidates.sort(key=lambda c: (TREND_PRIORITY.get(c['trend'], 99), c['unit_cost']))

    remaining = budget
    recommendations = []
    for c in candidates:
        if remaining <= 0:
            break
        # Fill as many units of this SKU as we can afford, up to the shortfall.
        affordable_qty = int(remaining // c['unit_cost'])
        qty = min(c['shortfall'], affordable_qty)
        if qty <= 0:
            continue

        line_total = round(qty * c['unit_cost'], 2)
        remaining = round(remaining - line_total, 2)
        lead_time = CATEGORY_LEAD_TIME_DAYS.get(c['category'], DEFAULT_LEAD_TIME_DAYS)

        recommendations.append({
            'sku': c['sku'],
            'name': c['name'],
            'category': c['category'],
            'trend': c['trend'],
            'unit_cost': c['unit_cost'],
            'quantity': qty,
            'line_total': line_total,
            'lead_time_days': lead_time,
        })

    return {
        'budget': budget,
        'spent': round(budget - remaining, 2),
        'remaining': remaining,
        'recommendations': recommendations,
    }


@app.post("/api/restock/orders", response_model=RestockOrder)
def submit_restock_order(req: SubmitRestockRequest):
    """Persist a restock order to disk and return the stored record."""
    if not req.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    total_cost = round(sum(item.line_total for item in req.items), 2)
    # The overall delivery date is driven by the slowest line item.
    max_lead = max(item.lead_time_days for item in req.items)
    now = datetime.utcnow()
    expected_delivery = (now + timedelta(days=max_lead)).strftime('%Y-%m-%d')

    order = {
        'id': str(uuid.uuid4())[:8],
        'submitted_at': now.strftime('%Y-%m-%dT%H:%M:%S'),
        'total_cost': total_cost,
        'budget': req.budget,
        'items': [item.model_dump() for item in req.items],
        'expected_delivery': expected_delivery,
        'max_lead_time_days': max_lead,
    }

    existing = _load_restock_orders()
    existing.append(order)
    _save_restock_orders(existing)

    return order


@app.get("/api/restock/orders", response_model=List[RestockOrder])
def list_restock_orders():
    """Return all submitted restock orders, newest first."""
    data = _load_restock_orders()
    # Reverse so most recent submissions appear at the top of the Orders tab.
    return list(reversed(data))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
