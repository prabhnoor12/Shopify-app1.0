"""
String utility functions for slugification, case conversion, and truncation.
"""

import re


def slugify(text: str) -> str:
    """
    Convert a string to a URL-friendly slug.
    """
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def to_camel_case(s: str) -> str:
    """
    Convert snake_case or space-separated string to camelCase.
    """
    s = re.sub(r"[_\s]+", " ", s).title().replace(" ", "")
    return s[0].lower() + s[1:] if s else ""


def to_snake_case(s: str) -> str:
    """
    Convert camelCase or space-separated string to snake_case.
    """
    s = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", s)
    s = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s)
    s = re.sub(r"[\s]+", "_", s)
    return s.lower()


def truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate a string to a max length, adding a suffix if needed.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix
