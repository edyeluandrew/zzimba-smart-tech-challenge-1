from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import HardwareOrder, OrderItem, OrderStatus
from app.schemas import OrderCreate, OrderRead

router = APIRouter()


@router.post("/store/order", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def place_order(payload: OrderCreate, db: Session = Depends(get_db)) -> HardwareOrder:
    line_items = [
        OrderItem(
            product_id=item.product_id,
            product_name=item.product_name,
            quantity=item.quantity,
            unit_price_ugx=item.unit_price_ugx,
            line_total_ugx=item.quantity * item.unit_price_ugx,
        )
        for item in payload.items
    ]
    order = HardwareOrder(
        contractor_id=payload.contractor_id,
        delivery_site_location=payload.delivery_site_location,
        total_amount_ugx=sum(item.line_total_ugx for item in line_items),
        status=OrderStatus.AWAITING_FULFILLMENT,
        items=line_items,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order
