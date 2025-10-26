"""
Service for managing app/shop/user settings.
"""

from sqlalchemy.orm import Session


class SettingService:
    def __init__(self, db: Session):
        self.db = db

    def create_setting(self, setting_data: dict):
        from my_app.crud.settings_crud import create_setting

        return create_setting(self.db, setting_data)

    def get_setting(self, setting_id: int):
        from my_app.crud.settings_crud import get_setting

        return get_setting(self.db, setting_id)

    def list_setting(self, skip: int = 0, limit: int = 100):
        from my_app.crud.settings_crud import get_setting

        return get_setting(self.db, skip=skip, limit=limit)

    def update_setting(self, setting_id: int, setting_update: dict):
        from my_app.crud.settings_crud import update_setting

        return update_setting(self.db, setting_id, setting_update)

    def delete_setting(self, setting_id: int):
        from my_app.crud.settings_crud import delete_setting

        return delete_setting(self.db, setting_id)
