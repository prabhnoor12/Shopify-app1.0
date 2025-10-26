from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import deps
from ..services.ab_testing_service import ABTestingService
from ..models.shop import ShopifyUser
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class VariantsData(BaseModel):
    description: str
    traffic_allocation: float


class ABTestCreate(BaseModel):
    product_id: int
    variants: list[VariantsData]
    start_time: datetime = None
    end_time: datetime = None


class ABTestUpdate(BaseModel):
    product_id: int = None
    variants: list[VariantsData] = None
    start_time: datetime = None
    end_time: datetime = None


@router.post("/ab-tests", response_model=dict)
def create_ab_test(
    ab_test_in: ABTestCreate,
    db: Session = Depends(deps.get_db),
    user: ShopifyUser = Depends(deps.get_current_user),
    ab_testing_service: ABTestingService = Depends(deps.get_ab_testing_service),
):
    """
    Create a new A/B test.
    """
    ab_test = ab_testing_service.create_ab_test(
        user_id=user.id,
        product_id=ab_test_in.product_id,
        variants_data=[variant.dict() for variant in ab_test_in.variants],
        start_time=ab_test_in.start_time,
        end_time=ab_test_in.end_time,
    )
    return {"id": ab_test.id}


@router.put("/ab-tests/{ab_test_id}", response_model=dict)
def update_ab_test(
    ab_test_id: int,
    ab_test_in: ABTestUpdate,
    db: Session = Depends(deps.get_db),
    user: ShopifyUser = Depends(deps.get_current_user),
    ab_testing_service: ABTestingService = Depends(deps.get_ab_testing_service),
):
    """
    Update an A/B test.
    """
    ab_test = ab_testing_service.update_ab_test(
        ab_test_id=ab_test_id,
        user_id=user.id,
        product_id=ab_test_in.product_id,
        variants_data=[variant.dict() for variant in ab_test_in.variants] if ab_test_in.variants else None,
        start_time=ab_test_in.start_time,
        end_time=ab_test_in.end_time,
    )
    if not ab_test:
        raise HTTPException(status_code=404, detail="A/B test not found.")
    return {"id": ab_test.id}


@router.delete("/ab-tests/{ab_test_id}", response_model=dict)
def delete_ab_test(
    ab_test_id: int,
    user: ShopifyUser = Depends(deps.get_current_user),
    ab_testing_service: ABTestingService = Depends(deps.get_ab_testing_service),
):
    """
    Delete an A/B test.
    """
    success = ab_testing_service.delete_ab_test(ab_test_id=ab_test_id, user_id=user.id)
    if not success:
        raise HTTPException(status_code=404, detail="A/B test not found or you do not have permission to delete it.")
    return {"message": "A/B test deleted successfully"}


@router.post("/experiments/{experiment_id}/start", response_model=dict)
def start_experiment(
    experiment_id: int,
    ab_testing_service: ABTestingService = Depends(deps.get_ab_testing_service),
):
    try:
        experiment = ab_testing_service.start_test(experiment_id)
        return {"id": experiment.id, "status": experiment.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/experiments/{experiment_id}/pause", response_model=dict)
def pause_experiment(
    experiment_id: int,
    ab_testing_service: ABTestingService = Depends(deps.get_ab_testing_service),
):
    try:
        experiment = ab_testing_service.pause_test(experiment_id)
        return {"id": experiment.id, "status": experiment.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/experiments/{experiment_id}/stop", response_model=dict)
def stop_experiment(
    experiment_id: int,
    ab_testing_service: ABTestingService = Depends(deps.get_ab_testing_service),
):
    try:
        experiment = ab_testing_service.end_test(experiment_id)
        return {"id": experiment.id, "status": experiment.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ab-tests/{ab_test_id}/recommendations", response_model=dict)
def get_test_recommendations(
    ab_test_id: int,
    user: ShopifyUser = Depends(deps.get_current_user),
    ab_testing_service: ABTestingService = Depends(deps.get_ab_testing_service),
):
    """
    Get recommendations for an A/B test.
    """
    recommendations = ab_testing_service.get_test_recommendations(ab_test_id=ab_test_id, user_id=user.id)
    if not recommendations:
        raise HTTPException(status_code=404, detail="No recommendations found for this test.")
    return recommendations


class DeclareWinnerData(BaseModel):
    variant_id: int


@router.post("/ab-tests/{ab_test_id}/declare-winner", response_model=dict)
async def declare_winner(
    ab_test_id: int,
    winner_data: DeclareWinnerData,
    user: ShopifyUser = Depends(deps.get_current_user),
    ab_testing_service: ABTestingService = Depends(deps.get_ab_testing_service),
):
    """
    Declare a winner for an A/B test.
    """
    try:
        result = await ab_testing_service.declare_winner(
            ab_test_id=ab_test_id,
            variant_id=winner_data.variant_id,
            user=user,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))



@router.get("/ab-tests/{ab_test_id}", response_model=dict)
def get_ab_test(
    ab_test_id: int,
    ab_testing_service: ABTestingService = Depends(deps.get_ab_testing_service),
):
    """
    Get a single A/B test by ID.
    """
    ab_test = ab_testing_service.get_test_by_id(ab_test_id)
    if not ab_test:
        raise HTTPException(status_code=404, detail="A/B test not found.")
    return ab_test


@router.get("/ab-tests", response_model=list[dict])
def get_all_ab_tests(
    user: ShopifyUser = Depends(deps.get_current_user),
    ab_testing_service: ABTestingService = Depends(deps.get_ab_testing_service),
):
    """
    Get all A/B tests for the current user.
    """
    return ab_testing_service.get_all_tests_for_user(user.id)


@router.get("/ab-tests/{ab_test_id}/results", response_model=dict)
def get_ab_test_results(
    ab_test_id: int,
    ab_testing_service: ABTestingService = Depends(deps.get_ab_testing_service),
):
    """
    Get the results of an A/B test.
    """
    results = ab_testing_service.get_test_results(ab_test_id)
    if not results:
        raise HTTPException(status_code=404, detail="Results not found for this test.")
    return results


@router.get("/ai-recommendations", response_model=list[dict])
def get_ai_recommendations(
    ab_testing_service: ABTestingService = Depends(deps.get_ab_testing_service),
):
    """
    Get general AI recommendations.
    """
    return ab_testing_service.get_general_ai_recommendations()


@router.post("/variants/{variant_id}/impression", response_model=dict)
def record_impression(
    variant_id: int,
    ab_testing_service: ABTestingService = Depends(deps.get_ab_testing_service),
):
    ab_testing_service.record_impression(variant_id)
    return {"message": "Impression recorded"}


@router.post("/variants/{variant_id}/click", response_model=dict)
def record_click(
    variant_id: int,
    ab_testing_service: ABTestingService = Depends(deps.get_ab_testing_service),
):
    ab_testing_service.record_click(variant_id)
    return {"message": "Click recorded"}


@router.post("/variants/{variant_id}/conversion", response_model=dict)
def record_conversion(
    variant_id: int,
    ab_testing_service: ABTestingService = Depends(deps.get_ab_testing_service),
):
    ab_testing_service.record_conversion(variant_id)
    return {"message": "Conversion recorded"}
