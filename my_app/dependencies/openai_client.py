"""
Shopify API dependencies for FastAPI routes.
"""

import os
from openai import OpenAI


def get_openai_client() -> OpenAI:
    """
    Dependency to get an OpenAI client instance using the API key from environment.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
    return OpenAI(api_key=api_key)
