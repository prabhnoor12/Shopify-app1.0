"""
API routes for audit log CRUD operations.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db

from ..schemas.audit import AuditLogCreate, AuditLogRead
from ..services.audit_service import AuditLogService as AuditService

router = APIRouter(prefix="/audit", tags=["audit"])


@router.post("/", response_model=AuditLogRead)
def create_audit(audit: AuditLogCreate, db: Session = Depends(get_db)):
    service = AuditService(db)
    return service.create_audit(audit.dict())


@router.get("/", response_model=List[AuditLogRead])
def list_audits(db: Session = Depends(get_db)):
    service = AuditService(db)
    return service.list_audits()


@router.get("/{audit_id}", response_model=AuditLogRead)
def get_audit(audit_id: int, db: Session = Depends(get_db)):
    service = AuditService(db)
    audit = service.get_audit(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit log not found.")
    return audit


@router.delete("/{audit_id}")
def delete_audit(audit_id: int, db: Session = Depends(get_db)):
    service = AuditService(db)
    audit = service.delete_audit(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit log not found.")
    return {"detail": "Audit deleted"}
    return {"detail": "Audit log deleted."}
