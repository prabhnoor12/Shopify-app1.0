"""
Utility function for tracking model changes.
"""

from sqlalchemy import inspect


from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.relationships import RelationshipProperty


def get_model_changes(
    model_instance,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    serialize: bool = False,
) -> dict:
    """
    Get the changes made to a model instance.

    Args:
        model_instance: The SQLAlchemy model instance.
        include: A list of field names to include. If provided, only these
                 fields will be tracked.
        exclude: A list of field names to exclude from tracking.
        serialize: If True, return a JSON-serializable dictionary.

    Returns:
        A dictionary of the changes, with field names as keys and
        tuples of (old_value, new_value) as values.
    """
    state = inspect(model_instance)
    changes = {}
    for attr in state.manager.attributes:
        if include and attr.key not in include:
            continue
        if exclude and attr.key in exclude:
            continue

        history = state.get_history(attr.key, True)
        if not history.has_changes():
            continue

        old_value = history.deleted[0] if history.deleted else None
        new_value = history.added[0] if history.added else None

        if old_value == new_value:
            continue

        if isinstance(getattr(model_instance.__class__, attr.key), InstrumentedAttribute):
            prop = getattr(model_instance.__class__, attr.key).property
            if isinstance(prop, RelationshipProperty):
                # For relationships, get the primary key of the related object
                if old_value:
                    old_value = inspect(old_value).identity
                if new_value:
                    new_value = inspect(new_value).identity

        if serialize:
            changes[attr.key] = {
                "old": str(old_value) if old_value is not None else None,
                "new": str(new_value) if new_value is not None else None,
            }
        else:
            changes[attr.key] = (old_value, new_value)
    return changes


def get_bulk_model_changes(
    model_instances: list,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
) -> list[dict]:
    """
    Get the changes made to a list of model instances.

    Args:
        model_instances: A list of SQLAlchemy model instances.
        include: A list of field names to include.
        exclude: A list of field names to exclude.

    Returns:
        A list of change dictionaries.
    """
    return [
        get_model_changes(instance, include=include, exclude=exclude)
        for instance in model_instances
    ]


def summarize_changes(changes: dict) -> str:
    """
    Create a human-readable summary of model changes.

    Args:
        changes: A dictionary of changes from get_model_changes.

    Returns:
        A string summarizing the changes.
    """
    if not changes:
        return "No changes detected."

    summary = ["Model changes:"]
    for field, (old, new) in changes.items():
        summary.append(f"  - {field}: '{old}' -> '{new}'")
    return "\n".join(summary)
