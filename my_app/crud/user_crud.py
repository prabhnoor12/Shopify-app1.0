
from sqlalchemy.orm import Session
from my_app.models.user import User
from datetime import datetime, timedelta



def activate_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_active = True
        db.commit()
        db.refresh(user)
    return user
 

def deactivate_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_active = False
        db.commit()
        db.refresh(user)
    return user

def update_password(db: Session, user_id: int, new_password: str):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.hashed_password = new_password
        db.commit()
        db.refresh(user)
    return user

def update_last_login(db: Session, user_id: int):
    from sqlalchemy.sql import func
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.last_login = func.now()
        db.commit()
        db.refresh(user)
    return user

def update_profile(db: Session, user_id: int, profile_data: dict):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        for key, value in profile_data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        db.commit()
        db.refresh(user)
    return user
from sqlalchemy.orm import Session
from my_app.models.user import User
from datetime import datetime, timedelta


def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user: dict):
    db_user = User(**user)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, user_update: dict):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        for key, value in user_update.items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user


def get_inactive_users(db: Session, days: int):
    """Retrieves users who have not logged in for a specified number of days."""
    delta = timedelta(days=days)
    cutoff_date = datetime.utcnow() - delta
    return db.query(User).filter(User.last_login < cutoff_date).all()
