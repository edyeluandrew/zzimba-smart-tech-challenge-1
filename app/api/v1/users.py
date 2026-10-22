from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import UserAccount
from app.schemas import UserProfile
from app.storage import blueprint_public_url

router = APIRouter()


@router.get("/users/profile/{user_id}", response_model=UserProfile)
def get_profile(user_id: int, db: Session = Depends(get_db)) -> UserProfile:
    user = db.get(UserAccount, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"User {user_id} was not found")

    # Hardcoded on purpose. This build mocks Laboremus and Verify.ug
    # instead of calling those trust networks.
    return UserProfile(
        user_id=user.id,
        name=user.name,
        role=user.role,
        is_identity_verified_by_laboremus=True,
        is_credentials_verified_by_verify_ug=True,
        cloud_storage_blueprint_url=blueprint_public_url(user.blueprint_object_key),
    )
