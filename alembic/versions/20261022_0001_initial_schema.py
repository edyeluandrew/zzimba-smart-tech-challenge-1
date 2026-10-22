"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-22

"""

from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contracts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("engineer_name", sa.String(length=200), nullable=False),
        sa.Column("client_name", sa.String(length=200), nullable=False),
        sa.Column("project_location", sa.String(length=300), nullable=False),
        sa.Column("milestone_title", sa.String(length=200), nullable=False),
        sa.Column("milestone_budget_ugx", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "hardware_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("contractor_id", sa.Integer(), nullable=False),
        sa.Column("delivery_site_location", sa.String(length=300), nullable=False),
        sa.Column("total_amount_ugx", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_hardware_orders_contractor_id", "hardware_orders", ["contractor_id"])
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("hardware_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("product_name", sa.String(length=200), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price_ugx", sa.Integer(), nullable=False),
        sa.Column("line_total_ugx", sa.Integer(), nullable=False),
    )
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("role", sa.String(length=120), nullable=False),
        sa.Column("blueprint_object_key", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "payment_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("transaction_reference", sa.String(length=120), nullable=False),
        sa.Column("payment_type", sa.String(length=40), nullable=False),
        sa.Column("reference_id", sa.Integer(), nullable=False),
        sa.Column("transaction_status", sa.String(length=40), nullable=False),
        sa.Column("applied", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_payment_events_transaction_reference", "payment_events", ["transaction_reference"], unique=True)
    op.create_index("ix_payment_events_reference_id", "payment_events", ["reference_id"])

    users = sa.table(
        "users",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("role", sa.String),
        sa.column("blueprint_object_key", sa.String),
        sa.column("created_at", sa.DateTime),
    )
    op.bulk_insert(
        users,
        [
            {
                "id": 4,
                "name": "Alex Mukasa",
                "role": "Civil Engineer",
                "blueprint_object_key": "engineers/4/site-blueprint.pdf",
                "created_at": datetime.now(timezone.utc),
            }
        ],
    )


def downgrade() -> None:
    op.drop_table("payment_events")
    op.drop_table("users")
    op.drop_table("order_items")
    op.drop_table("hardware_orders")
    op.drop_table("contracts")
