from sqlalchemy.orm import Session
from my_app.models.setting import Setting


def get_setting(db: Session, setting_id: int):
    return db.query(Setting).filter(Setting.id == setting_id).first()


def get_settings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Setting).offset(skip).limit(limit).all()


def create_setting(db: Session, setting: dict):
    db_setting = Setting(**setting)
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting


def update_setting(db: Session, setting_id: int, setting_update: dict):
    db_setting = db.query(Setting).filter(Setting.id == setting_id).first()
    if db_setting:
        for key, value in setting_update.items():
            setattr(db_setting, key, value)
        db.commit()
        db.refresh(db_setting)
    return db_setting


def delete_setting(db: Session, setting_id: int):
    db_setting = db.query(Setting).filter(Setting.id == setting_id).first()
    if db_setting:
        db.delete(db_setting)
        db.commit()
    return db_setting
