"""
CORS middleware setup for FastAPI.
"""

from fastapi.middleware.cors import CORSMiddleware


def add_cors_middleware(app):
    """
    Adds CORS middleware to the FastAPI app with default settings.
    Modify origins, methods, and headers as needed.
    """
    # Allow Shopify, local frontend, and ngrok/Cloudflare tunnel URLs
    allowed_origins = [
        "https://admin.shopify.com",
        
        "https://127.0.0.1:5173",
        "http://127.0.0.1:5173",
        "https://localhost:5173",
        "http://localhost:5173",
        # Add your public tunnel URL here, e.g. "https://xxxx.ngrok.io"
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
