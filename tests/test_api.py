import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import UserAccount

CONTRACT_BODY = {
    "engineer_name": "John Doe",
    "client_name": "Luweero Property Developers Ltd",
    "project_location": "Luweero Town",
    "milestone_title": "Foundation Concrete Pour",
    "milestone_budget_ugx": 3500000,
}

ORDER_BODY = {
    "contractor_id": 12,
    "delivery_site_location": "Wobulenzi, Luweero",
    "items": [
        {
            "product_id": 101,
            "product_name": "Tororo Cement Bag",
            "quantity": 50,
            "unit_price_ugx": 32000,
        },
        {
            "product_id": 204,
            "product_name": "Electrical Conduit Pipe",
            "quantity": 15,
            "unit_price_ugx": 8500,
        },
    ],
}


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    db = session_factory()
    db.add(
        UserAccount(
            id=4,
            name="Alex Mukasa",
            role="Civil Engineer",
            blueprint_object_key="engineers/4/site-blueprint.pdf",
        )
    )
    db.commit()
    db.close()

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_health(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_contract_starts_pending_payment(client: TestClient):
    response = client.post("/api/v1/contracts/create", json=CONTRACT_BODY)
    assert response.status_code == 201
    body = response.json()
    assert body["engineer_name"] == "John Doe"
    assert body["milestone_budget_ugx"] == 3500000
    assert body["status"] == "PENDING_PAYMENT"
    assert body["id"] >= 1


def test_create_contract_rejects_location_outside_luweero(client: TestClient):
    payload = {**CONTRACT_BODY, "project_location": "Kampala Industrial Area"}
    response = client.post("/api/v1/contracts/create", json=payload)
    assert response.status_code == 422


def test_create_contract_accepts_luweero_regardless_of_case(client: TestClient):
    payload = {**CONTRACT_BODY, "project_location": "wobulenzi, luweero"}
    response = client.post("/api/v1/contracts/create", json=payload)
    assert response.status_code == 201


def test_place_order_calculates_total_and_awaits_fulfillment(client: TestClient):
    response = client.post("/api/v1/store/order", json=ORDER_BODY)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "AWAITING_FULFILLMENT"
    assert body["total_amount_ugx"] == 1_727_500
    assert body["items"][0]["line_total_ugx"] == 1_600_000
    assert body["items"][1]["line_total_ugx"] == 127_500


def test_escrow_webhook_locks_contract(client: TestClient):
    created = client.post("/api/v1/contracts/create", json=CONTRACT_BODY).json()
    response = client.post(
        "/api/v1/mock-payment/webhook",
        json={
            "transaction_reference": "TXN-YO-112233",
            "payment_type": "ESCROW_LOCK",
            "reference_id": created["id"],
            "transaction_status": "SUCCESS",
        },
    )
    assert response.status_code == 200
    assert response.json()["applied"] is True
    assert response.json()["record_status"] == "ESCROW_LOCKED"


def test_store_webhook_marks_order_paid(client: TestClient):
    created = client.post("/api/v1/store/order", json=ORDER_BODY).json()
    response = client.post(
        "/api/v1/mock-payment/webhook",
        json={
            "transaction_reference": "TXN-YO-445566",
            "payment_type": "STORE_PURCHASE",
            "reference_id": created["id"],
            "transaction_status": "SUCCESS",
        },
    )
    assert response.status_code == 200
    assert response.json()["record_status"] == "PAID_PROCESSING"


def test_failed_payment_does_not_change_status_until_success(client: TestClient):
    created = client.post("/api/v1/contracts/create", json=CONTRACT_BODY).json()
    failed = client.post(
        "/api/v1/mock-payment/webhook",
        json={
            "transaction_reference": "TXN-YO-778899",
            "payment_type": "ESCROW_LOCK",
            "reference_id": created["id"],
            "transaction_status": "FAILED",
        },
    )
    assert failed.status_code == 200
    assert failed.json()["applied"] is False
    assert failed.json()["record_status"] == "PENDING_PAYMENT"

    paid = client.post(
        "/api/v1/mock-payment/webhook",
        json={
            "transaction_reference": "TXN-YO-778899",
            "payment_type": "ESCROW_LOCK",
            "reference_id": created["id"],
            "transaction_status": "SUCCESS",
        },
    )
    assert paid.status_code == 200
    assert paid.json()["applied"] is True
    assert paid.json()["record_status"] == "ESCROW_LOCKED"


def test_webhook_replay_is_idempotent(client: TestClient):
    created = client.post("/api/v1/contracts/create", json=CONTRACT_BODY).json()
    payload = {
        "transaction_reference": "TXN-YO-REPLAY",
        "payment_type": "ESCROW_LOCK",
        "reference_id": created["id"],
        "transaction_status": "SUCCESS",
    }
    first = client.post("/api/v1/mock-payment/webhook", json=payload)
    second = client.post("/api/v1/mock-payment/webhook", json=payload)
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["record_status"] == "ESCROW_LOCKED"


def test_webhook_rejects_conflicting_replay(client: TestClient):
    created = client.post("/api/v1/contracts/create", json=CONTRACT_BODY).json()
    client.post(
        "/api/v1/mock-payment/webhook",
        json={
            "transaction_reference": "TXN-YO-CONFLICT",
            "payment_type": "ESCROW_LOCK",
            "reference_id": created["id"],
            "transaction_status": "SUCCESS",
        },
    )
    conflict = client.post(
        "/api/v1/mock-payment/webhook",
        json={
            "transaction_reference": "TXN-YO-CONFLICT",
            "payment_type": "STORE_PURCHASE",
            "reference_id": created["id"],
            "transaction_status": "SUCCESS",
        },
    )
    assert conflict.status_code == 409


def test_webhook_missing_contract_is_404(client: TestClient):
    response = client.post(
        "/api/v1/mock-payment/webhook",
        json={
            "transaction_reference": "TXN-YO-MISSING",
            "payment_type": "ESCROW_LOCK",
            "reference_id": 9999,
            "transaction_status": "SUCCESS",
        },
    )
    assert response.status_code == 404


def test_profile_returns_trust_flags_and_blueprint_url(client: TestClient, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(
        settings,
        "cloud_storage_public_base_url",
        "https://cdn.example.com/blueprints",
    )
    response = client.get("/api/v1/users/profile/4")
    assert response.status_code == 200
    assert response.json() == {
        "user_id": 4,
        "name": "Alex Mukasa",
        "role": "Civil Engineer",
        "is_identity_verified_by_laboremus": True,
        "is_credentials_verified_by_verify_ug": True,
        "cloud_storage_blueprint_url": "https://cdn.example.com/blueprints/engineers/4/site-blueprint.pdf",
    }


def test_missing_profile_is_404(client: TestClient):
    response = client.get("/api/v1/users/profile/404")
    assert response.status_code == 404
