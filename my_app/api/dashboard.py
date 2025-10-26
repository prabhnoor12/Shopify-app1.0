from typing import List, Dict, Optional
from fastapi import APIRouter, Depends
from ..services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_dashboard_service():
    return DashboardService()


@router.get("/user/{user_id}", response_model=Dict)
def get_user_dashboard(
    user_id: int, service: DashboardService = Depends(get_dashboard_service)
):
    # redacted
    return service.get_user_dashboard(user_id)


@router.get("/user/{user_id}/summary", response_model=Dict)
def get_user_summary(
    user_id: int, service: DashboardService = Depends(get_dashboard_service)
):
    # redacted
    return service.get_user_summary(user_id)


@router.get("/user/{user_id}/activity", response_model=Dict)
def get_activity_summary(
    user_id: int, service: DashboardService = Depends(get_dashboard_service)
):
    # redacted
    return service.get_activity_summary(user_id)


@router.get("/user/{user_id}/recent-descriptions", response_model=List[Dict])
def get_recent_descriptions(
    user_id: int,
    limit: int = 5,
    service: DashboardService = Depends(get_dashboard_service),
):
    # redacted
    return service.get_recent_descriptions(user_id, limit)


@router.get("/team/{team_id}/activity", response_model=List[Dict])
def get_team_activity(
    team_id: int, service: DashboardService = Depends(get_dashboard_service)
):
    # redacted
    return service.get_team_activity(team_id)


@router.get("/descriptions/monthly-counts", response_model=List[int])
def get_monthly_description_counts(
    user_id: Optional[int] = None,
    days: int = 30,
    service: DashboardService = Depends(get_dashboard_service),
):
    # redacted
    return service.get_monthly_description_counts(user_id, days)


@router.get("/top-products", response_model=List[Dict])
def get_top_products(
    limit: int = 5,
    by: str = "sales",
    service: DashboardService = Depends(get_dashboard_service),
):
    """Get top products by sales or views."""
    return service.get_top_products(limit, by)


@router.get("/recent-orders", response_model=List[Dict])
def get_recent_orders(
    limit: int = 5,
    service: DashboardService = Depends(get_dashboard_service),
):
    """Get recent orders with customer, product, and order value."""
    return service.get_recent_orders(limit)


@router.get("/sales-trend", response_model=List[Dict])
def get_sales_trend(
    days: int = 30,
    service: DashboardService = Depends(get_dashboard_service),
):
    """Get sales/revenue per day for the last N days."""
    return service.get_sales_trend(days)
