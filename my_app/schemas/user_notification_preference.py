from pydantic import ConfigDict, BaseModel


class UserNotificationPreferenceBase(BaseModel):
    email_enabled: bool = True
    sms_enabled: bool = False


class UserNotificationPreferenceCreate(UserNotificationPreferenceBase):
    pass


class UserNotificationPreferenceUpdate(UserNotificationPreferenceBase):
    pass


class UserNotificationPreference(UserNotificationPreferenceBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)
