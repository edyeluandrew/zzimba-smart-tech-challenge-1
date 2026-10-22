import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

_LUWEERO = re.compile(r"\bluweero\b", re.IGNORECASE)


class ContractCreate(BaseModel):
    engineer_name: str = Field(min_length=1, max_length=200)
    client_name: str = Field(min_length=1, max_length=200)
    project_location: str = Field(min_length=1, max_length=300)
    milestone_title: str = Field(min_length=1, max_length=200)
    milestone_budget_ugx: int = Field(gt=0, le=10_000_000_000)

    @field_validator("engineer_name", "client_name", "project_location", "milestone_title", mode="before")
    @classmethod
    def strip_text(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("project_location")
    @classmethod
    def location_must_mention_luweero(cls, value: str) -> str:
        if _LUWEERO.search(value) is None:
            raise ValueError("project_location must contain the word 'Luweero'")
        return value


class ContractRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    engineer_name: str
    client_name: str
    project_location: str
    milestone_title: str
    milestone_budget_ugx: int
    status: str


class OrderItemIn(BaseModel):
    product_id: int = Field(gt=0)
    product_name: str = Field(min_length=1, max_length=200)
    quantity: int = Field(gt=0, le=1_000_000)
    unit_price_ugx: int = Field(gt=0, le=10_000_000_000)

    @field_validator("product_name", mode="before")
    @classmethod
    def strip_name(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value


class OrderCreate(BaseModel):
    contractor_id: int = Field(gt=0)
    delivery_site_location: str = Field(min_length=1, max_length=300)
    items: list[OrderItemIn] = Field(min_length=1)

    @field_validator("delivery_site_location", mode="before")
    @classmethod
    def strip_location(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    product_name: str
    quantity: int
    unit_price_ugx: int
    line_total_ugx: int


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contractor_id: int
    delivery_site_location: str
    total_amount_ugx: int
    status: str
    items: list[OrderItemRead]


class WebhookPayload(BaseModel):
    transaction_reference: str = Field(min_length=1, max_length=120)
    payment_type: str = Field(pattern="^(ESCROW_LOCK|STORE_PURCHASE)$")
    reference_id: int = Field(gt=0)
    transaction_status: str = Field(min_length=1, max_length=40)

    @field_validator("transaction_reference", "transaction_status", mode="before")
    @classmethod
    def strip_values(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("transaction_status")
    @classmethod
    def normalize_status(cls, value: str) -> str:
        return value.upper()


class WebhookResult(BaseModel):
    transaction_reference: str
    payment_type: str
    reference_id: int
    transaction_status: str
    applied: bool
    record_status: str | None = None


class UserProfile(BaseModel):
    user_id: int
    name: str
    role: str
    is_identity_verified_by_laboremus: bool
    is_credentials_verified_by_verify_ug: bool
    cloud_storage_blueprint_url: str
