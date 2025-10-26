from typing import Dict, List, TypedDict, Optional


class PermissionDict(TypedDict):
    resource: str
    action: str
    scope: Optional[str]  # Add optional scope field


class RoleTemplate(TypedDict):
    name: str
    description: str
    permissions: List[PermissionDict]


ROLE_TEMPLATES: Dict[str, RoleTemplate] = {
    "Admin": {
        "name": "Admin",
        "description": "Full access to all resources and settings.",
        "permissions": [
            {"resource": "team", "action": "create", "scope": None},
            {"resource": "team", "action": "read", "scope": None},
            {"resource": "team", "action": "update", "scope": None},
            {"resource": "team", "action": "delete", "scope": None},
            {"resource": "team.member", "action": "create", "scope": None},
            {"resource": "team.member", "action": "read", "scope": None},
            {"resource": "team.member", "action": "update", "scope": None},
            {"resource": "team.member", "action": "delete", "scope": None},
            {"resource": "team.custom_role", "action": "create", "scope": None},
            {"resource": "team.custom_role", "action": "read", "scope": None},
            {"resource": "team.custom_role", "action": "update", "scope": None},
            {"resource": "team.custom_role", "action": "delete", "scope": None},
        ],
    },
    "Editor": {
        "name": "Editor",
        "description": "Can create and edit resources, but cannot manage team members or settings.",
        "permissions": [
            {"resource": "product", "action": "create", "scope": None},
            {"resource": "product", "action": "read", "scope": None},
            {"resource": "product", "action": "update", "scope": None},
            {"resource": "product", "action": "delete", "scope": None},
        ],
    },
    "Viewer": {
        "name": "Viewer",
        "description": "Can view resources, but cannot make any changes.",
        "permissions": [
            {"resource": "product", "action": "read", "scope": None},
            {"resource": "team.member", "action": "read", "scope": None},
        ],
    },
    "Guest": {
        "name": "Guest",
        "description": "Limited access to specific resources.",
        "permissions": [],
    },
}
