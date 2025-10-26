"""
This package contains CRUD (Create, Read, Update, Delete) operations
for the application's database models.

Each file in this package should correspond to a single model and
contain the functions for interacting with it.
"""

from . import usage_crud as usage
from . import shop_crud as shop
from . import subscription_crud as subscription
from . import usage_event_crud as usage_event
from . import plan_crud as plan
from . import role_crud as role
from . import permission_crud as permission
from . import user_crud as user
from . import team_crud as team
