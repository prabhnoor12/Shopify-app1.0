"""
API routes for consent management - GDPR compliance.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.consent_service import ConsentService
from ..schemas.consent import (
    ConsentPreferences,
    ConsentUpdateRequest,
    ConsentWithdrawRequest,
    ConsentResponse,
    ObjectionRequest
)
from ..utils.security import get_current_user
from ..models.shop import ShopifyUser

router = APIRouter(prefix="/consent", tags=["consent"])


@router.get("/preferences", response_model=ConsentResponse)
def get_consent_preferences(current_user: ShopifyUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get current consent preferences for the authenticated user.
    """
    service = ConsentService(db)
    consent = service.get_user_consent(current_user.id)

    if not consent:
        # Return default preferences
        return ConsentResponse(
            user_id=current_user.id,
            preferences=ConsentPreferences(),
            consent_version="1.0"
        )

    return ConsentResponse(
        user_id=current_user.id,
        preferences=ConsentPreferences(
            necessary_cookies=consent.necessary_cookies,
            analytics_cookies=consent.analytics_cookies,
            marketing_cookies=consent.marketing_cookies,
            functional_cookies=consent.functional_cookies,
            marketing_emails=consent.marketing_emails,
            product_updates=consent.product_updates,
            third_party_sharing=consent.third_party_sharing,
            profiling=consent.profiling,
            object_marketing=consent.object_marketing,
            object_profiling=consent.object_profiling,
        ),
        created_at=consent.created_at,
        updated_at=consent.updated_at,
        consent_version=consent.consent_version
    )


@router.put("/preferences", response_model=ConsentResponse)
def update_consent_preferences(
    request: ConsentUpdateRequest,
    current_user: ShopifyUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update consent preferences for the authenticated user.
    """
    service = ConsentService(db)

    # Convert Pydantic model to dict
    consent_data = request.preferences.dict()

    consent = service.create_or_update_consent(
        user_id=current_user.id,
        consent_data=consent_data,
        ip_address=request.ip_address,
        user_agent=request.user_agent
    )

    return ConsentResponse(
        user_id=current_user.id,
        preferences=ConsentPreferences(
            necessary_cookies=consent.necessary_cookies,
            analytics_cookies=consent.analytics_cookies,
            marketing_cookies=consent.marketing_cookies,
            functional_cookies=consent.functional_cookies,
            marketing_emails=consent.marketing_emails,
            product_updates=consent.product_updates,
            third_party_sharing=consent.third_party_sharing,
            profiling=consent.profiling,
            object_marketing=consent.object_marketing,
            object_profiling=consent.object_profiling,
        ),
        created_at=consent.created_at,
        updated_at=consent.updated_at,
        consent_version=consent.consent_version
    )


@router.post("/withdraw")
def withdraw_consent(
    request: ConsentWithdrawRequest,
    current_user: ShopifyUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Withdraw specific consent for the authenticated user.
    """
    service = ConsentService(db)

    # Validate consent type
    valid_types = [
        "analytics_cookies", "marketing_cookies", "functional_cookies",
        "marketing_emails", "product_updates", "third_party_sharing", "profiling"
    ]

    if request.consent_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid consent type. Valid types: {', '.join(valid_types)}")

    success = service.withdraw_consent(current_user.id, request.consent_type)

    if not success:
        raise HTTPException(status_code=404, detail="Consent preferences not found for user.")

    return {"detail": f"Successfully withdrew consent for {request.consent_type}"}


@router.get("/check/{consent_type}")
def check_consent(
    consent_type: str,
    current_user: ShopifyUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if user has given consent for a specific type.
    """
    service = ConsentService(db)

    valid_types = [
        "necessary_cookies", "analytics_cookies", "marketing_cookies", "functional_cookies",
        "marketing_emails", "product_updates", "third_party_sharing", "profiling"
    ]

    if consent_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid consent type. Valid types: {', '.join(valid_types)}")

    has_consent = service.has_consent(current_user.id, consent_type)

    return {"consent_type": consent_type, "has_consent": has_consent}


@router.post("/object")
def object_to_processing(
    request: ObjectionRequest,
    current_user: ShopifyUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Exercise the right to object to data processing.
    """
    service = ConsentService(db)

    # Validate objection type
    valid_types = ["marketing", "profiling"]
    if request.objection_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid objection type. Valid types: {', '.join(valid_types)}")

    success = service.object_to_processing(current_user.id, request.objection_type)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to record objection.")

    return {"detail": f"Successfully recorded objection to {request.objection_type} processing."}


@router.get("/objection/{objection_type}")
def check_objection(
    objection_type: str,
    current_user: ShopifyUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if user has objected to specific processing.
    """
    service = ConsentService(db)

    valid_types = ["marketing", "profiling"]
    if objection_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid objection type. Valid types: {', '.join(valid_types)}")

    has_objection = service.has_objection(current_user.id, objection_type)

    return {"objection_type": objection_type, "has_objection": has_objection}
