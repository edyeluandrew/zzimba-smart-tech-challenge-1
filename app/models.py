from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ContractStatus:
    PENDING_PAYMENT = "PENDING_PAYMENT"
    ESCROW_LOCKED = "ESCROW_LOCKED"


class OrderStatus:
    AWAITING_FULFILLMENT = "AWAITING_FULFILLMENT"
    PAID_PROCESSING = "PAID_PROCESSING"


class PaymentType:
    ESCROW_LOCK = "ESCROW_LOCK"
    STORE_PURCHASE = "STORE_PURCHASE"


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(primary_key=True)
    engineer_name: Mapped[str] = mapped_column(String(200))
    client_name: Mapped[str] = mapped_column(String(200))
    project_location: Mapped[str] = mapped_column(String(300))
    milestone_title: Mapped[str] = mapped_column(String(200))
    milestone_budget_ugx: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(40), default=ContractStatus.PENDING_PAYMENT)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
    )


class HardwareOrder(Base):
    __tablename__ = "hardware_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    contractor_id: Mapped[int] = mapped_column(Integer, index=True)
    delivery_site_location: Mapped[str] = mapped_column(String(300))
    total_amount_ugx: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(40), default=OrderStatus.AWAITING_FULFILLMENT)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
    )

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("hardware_orders.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(Integer)
    product_name: Mapped[str] = mapped_column(String(200))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price_ugx: Mapped[int] = mapped_column(Integer)
    line_total_ugx: Mapped[int] = mapped_column(Integer)

    order: Mapped[HardwareOrder] = relationship(back_populates="items")


class UserAccount(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(120))
    blueprint_object_key: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PaymentEvent(Base):
    __tablename__ = "payment_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_reference: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    payment_type: Mapped[str] = mapped_column(String(40))
    reference_id: Mapped[int] = mapped_column(Integer, index=True)
    transaction_status: Mapped[str] = mapped_column(String(40))
    applied: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
