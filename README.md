# Luweero Build API

This service is the escrow and hardware-store backend for Luweero Build. A civil engineer opens a milestone contract. A contractor places a materials order. A Yo! Payments callback marks the matching record paid. A profile returns the engineer, two mocked trust flags, and a link to the blueprint file.

## Setup

From the project folder, in PowerShell:

```
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open .env. Set DATABASE_URL to the Neon pooled connection string. The host name contains pooler. Set DIRECT_DATABASE_URL to the direct Neon string, the same database with pooler removed from the host. Leave the storage keys empty until a bucket exists. Then:

```
alembic upgrade head
uvicorn app.main:app --reload
```

The API listens on http://127.0.0.1:8000. The docs are at http://127.0.0.1:8000/docs.

The migration creates the tables and inserts Alex Mukasa as user 4.

If PowerShell blocks activation, call the virtualenv Python directly:

```
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Environment

Copy .env.example to .env. Real passwords and storage keys stay in .env. That file is not committed.

DATABASE_URL is the database the running API uses. Production is the Neon pooled URL. The local default is sqlite:///./luweero.db so the app can start before Neon is filled in.

DIRECT_DATABASE_URL is the Neon direct URL. Alembic uses it so migrations do not go through the pooler. Leave it blank only when DATABASE_URL is still SQLite.

CLOUD_STORAGE_PUBLIC_BASE_URL is the public prefix of the blueprint bucket, with no file name on the end.

CLOUD_STORAGE_BUCKET is the bucket name.

CLOUD_STORAGE_ACCESS_KEY_ID and CLOUD_STORAGE_SECRET_ACCESS_KEY are the Spaces credentials. Leave both empty for a local run.

APP_ENV is development or production.

## Endpoints

Every route is under the prefix /api/v1.

Create a milestone contract with POST /api/v1/contracts/create. The location must contain the word Luweero. The row is saved in the contracts table with status PENDING_PAYMENT.

```
{
  "engineer_name": "John Doe",
  "client_name": "Luweero Property Developers Ltd",
  "project_location": "Luweero Town",
  "milestone_title": "Foundation Concrete Pour",
  "milestone_budget_ugx": 3500000
}
```

Place a hardware order with POST /api/v1/store/order. The server adds up each line. For the sample below, 50 bags at 32000 plus 15 pipes at 8500 comes to 1727500 shillings. The order is saved with status AWAITING_FULFILLMENT, and each item is saved on its own row.

```
{
  "contractor_id": 12,
  "delivery_site_location": "Wobulenzi, Luweero",
  "items": [
    {"product_id": 101, "product_name": "Tororo Cement Bag", "quantity": 50, "unit_price_ugx": 32000},
    {"product_id": 204, "product_name": "Electrical Conduit Pipe", "quantity": 15, "unit_price_ugx": 8500}
  ]
}
```

Receive a payment callback with POST /api/v1/mock-payment/webhook. This stands in for Yo! Payments. When payment_type is ESCROW_LOCK, reference_id is the contract id and a SUCCESS result sets that contract to ESCROW_LOCKED. When payment_type is STORE_PURCHASE, reference_id is the hardware order id and a SUCCESS result sets that order to PAID_PROCESSING. Use the id returned by the create call. Any other transaction_status is stored and does not move the record. Sending the same successful transaction_reference again does not apply the money twice.

```
{
  "transaction_reference": "TXN-YO-112233",
  "payment_type": "ESCROW_LOCK",
  "reference_id": 1,
  "transaction_status": "SUCCESS"
}
```

Fetch a profile with GET /api/v1/users/profile/4. The name and role come from the users table. is_identity_verified_by_laboremus and is_credentials_verified_by_verify_ug are hardcoded true. The blueprint URL is CLOUD_STORAGE_PUBLIC_BASE_URL plus the file key stored on that user.

## Tests and migrations

```
python -m pytest -q
alembic upgrade head
```

## Pipeline

GitHub Actions runs the test suite on every push and every pull request. The workflow file is .github/workflows/ci.yml.

Render hosts the service from render.yaml, in Frankfurt, on the free plan. It deploys main only after that test check passes. The build installs dependencies. Before the new instance takes traffic, Alembic runs against DIRECT_DATABASE_URL. The process then starts with Uvicorn on the port Render provides. Render calls GET /health to decide the instance is ready.

Create the service once in the Render dashboard with New, then Blueprint, and select this repository. When Render asks for environment values, set DATABASE_URL to the Neon pooled URL and DIRECT_DATABASE_URL to the Neon direct URL. The storage values can stay as they are in .env.example until a bucket exists. After that first connection, a push to main tests and then deploys on its own.

## Architectural note

Render hosts the API in Frankfurt. The process is stateless. Secrets come from the environment, and blueprint files are not written onto the server disk. A push to main deploys only after the GitHub test check passes. The blueprint then installs dependencies, runs the migration, and starts the app.

DigitalOcean Spaces is the choice for the blueprint files. A drawing is a file, so it belongs in object storage. Spaces in Frankfurt gives each file a stable public URL. The profile endpoint builds that URL from CLOUD_STORAGE_PUBLIC_BASE_URL plus the file key stored on the user. Access keys stay in the environment.

A live Spaces bucket is not part of this submission. Spaces bills five dollars a month from the moment the first bucket exists, and this brief asks for the URL and the reason, not a funded account. The sample profile still returns the dynamic URL. Creating the bucket later means filling in the four storage variables and uploading engineers/4/site-blueprint.pdf. No application code has to change.

Neon Postgres, also in Frankfurt, stores the contracts, orders, line items, users, and payment events. Those rows need transactions, foreign keys, and backups. SQLAlchemy maps each table to a Python class, and Alembic creates the tables from those classes. Amounts are whole Uganda shillings. The same models run on SQLite in the test suite, which never needs the Neon password.
