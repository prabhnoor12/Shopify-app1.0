from sqlalchemy.orm import Session
from .. import schemas
from ..models.plan import Plan


def get_plan(db: Session, plan_id: int) -> Plan | None:
    return db.query(Plan).filter(Plan.id == plan_id).first()


def get_all_plans(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Plan).offset(skip).limit(limit).all()


def create_plan(db: Session, plan: schemas.PlanCreate) -> Plan:
    db_plan = Plan(**plan.dict())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan
