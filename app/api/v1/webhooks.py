from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Contract,
    ContractStatus,
    HardwareOrder,
    OrderStatus,
    PaymentEvent,
    PaymentType,
)
from app.schemas import WebhookPayload, WebhookResult

router = APIRouter()


def _same_payload(existing: PaymentEvent, payload: WebhookPayload) -> bool:
    return (
        existing.payment_type == payload.payment_type
        and existing.reference_id == payload.reference_id
        and existing.transaction_status == payload.transaction_status
    )


def _record_status(db: Session, payment_type: str, reference_id: int) -> str | None:
    if payment_type == PaymentType.ESCROW_LOCK:
        contract = db.get(Contract, reference_id)
        return None if contract is None else contract.status
    order = db.get(HardwareOrder, reference_id)
    return None if order is None else order.status


def _save_event(db: Session, existing: PaymentEvent | None, payload: WebhookPayload, applied: bool) -> None:
    if existing is None:
        db.add(
            PaymentEvent(
                transaction_reference=payload.transaction_reference,
                payment_type=payload.payment_type,
                reference_id=payload.reference_id,
                transaction_status=payload.transaction_status,
                applied=applied,
            )
        )
        return
    existing.payment_type = payload.payment_type
    existing.reference_id = payload.reference_id
    existing.transaction_status = payload.transaction_status
    existing.applied = applied


@router.post("/mock-payment/webhook", response_model=WebhookResult)
def payment_webhook(payload: WebhookPayload, db: Session = Depends(get_db)) -> WebhookResult:
    existing = db.scalar(
        select(PaymentEvent).where(PaymentEvent.transaction_reference == payload.transaction_reference)
    )
    if existing is not None and _same_payload(existing, payload):
        return WebhookResult(
            transaction_reference=payload.transaction_reference,
            payment_type=payload.payment_type,
            reference_id=payload.reference_id,
            transaction_status=payload.transaction_status,
            applied=existing.applied,
            record_status=_record_status(db, payload.payment_type, payload.reference_id),
        )
    if existing is not None and existing.applied:
        raise HTTPException(
            status_code=409,
            detail="transaction_reference was already applied with a different payload",
        )

    if payload.transaction_status != "SUCCESS":
        _save_event(db, existing, payload, applied=False)
        db.commit()
        return WebhookResult(
            transaction_reference=payload.transaction_reference,
            payment_type=payload.payment_type,
            reference_id=payload.reference_id,
            transaction_status=payload.transaction_status,
            applied=False,
            record_status=_record_status(db, payload.payment_type, payload.reference_id),
        )

    if payload.payment_type == PaymentType.ESCROW_LOCK:
        contract = db.get(Contract, payload.reference_id)
        if contract is None:
            raise HTTPException(status_code=404, detail=f"Contract {payload.reference_id} was not found")
        contract.status = ContractStatus.ESCROW_LOCKED
        record_status = contract.status
    elif payload.payment_type == PaymentType.STORE_PURCHASE:
        order = db.get(HardwareOrder, payload.reference_id)
        if order is None:
            raise HTTPException(status_code=404, detail=f"Hardware order {payload.reference_id} was not found")
        order.status = OrderStatus.PAID_PROCESSING
        record_status = order.status
    else:
        raise HTTPException(status_code=422, detail="Unsupported payment_type")

    _save_event(db, existing, payload, applied=True)
    db.commit()
    return WebhookResult(
        transaction_reference=payload.transaction_reference,
        payment_type=payload.payment_type,
        reference_id=payload.reference_id,
        transaction_status=payload.transaction_status,
        applied=True,
        record_status=record_status,
    )
