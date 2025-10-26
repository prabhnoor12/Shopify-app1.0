"""
API routes for session CRUD operations.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db

from ..schemas.session import SessionCreate, SessionRead
from ..services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/", response_model=SessionRead)
def create_session(session: SessionCreate, db: Session = Depends(get_db)):
    service = SessionService(db)
    return service.create_session(session.dict())


@router.get("/", response_model=List[SessionRead])
def list_sessions(db: Session = Depends(get_db)):
    service = SessionService(db)
    return service.list_sessions()


@router.get("/{session_id}", response_model=SessionRead)
def get_session(session_id: int, db: Session = Depends(get_db)):
    service = SessionService(db)
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return session


@router.delete("/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    service = SessionService(db)
    session = service.delete_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"detail": "Session deleted"}
    return {"detail": "Session deleted."}
