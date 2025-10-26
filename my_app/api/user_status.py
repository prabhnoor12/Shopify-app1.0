from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.user_service import UserService

router = APIRouter()

@router.get("/status")
def get_user_status(request: Request, db: Session = Depends(get_db)):
    shop = request.query_params.get("shop") or request.cookies.get("shop")
    if not shop:
        raise HTTPException(status_code=401, detail="Shop not provided.")
    service = UserService(db)
    user = service.get_user_by_shop_domain(shop)
    if not user:
        raise HTTPException(status_code=401, detail="User not authenticated.")
    return {"authenticated": True, "shop": shop}
