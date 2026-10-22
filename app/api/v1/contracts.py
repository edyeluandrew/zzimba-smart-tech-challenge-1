from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Contract, ContractStatus
from app.schemas import ContractCreate, ContractRead

router = APIRouter()


@router.post("/contracts/create", response_model=ContractRead, status_code=status.HTTP_201_CREATED)
def create_contract(payload: ContractCreate, db: Session = Depends(get_db)) -> Contract:
    contract = Contract(
        engineer_name=payload.engineer_name,
        client_name=payload.client_name,
        project_location=payload.project_location,
        milestone_title=payload.milestone_title,
        milestone_budget_ugx=payload.milestone_budget_ugx,
        status=ContractStatus.PENDING_PAYMENT,
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract
