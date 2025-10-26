class ShopifyAppException(Exception):
    """Base exception for Shopify app errors."""

    def __init__(self, message: str = None, code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message or self.__class__.__doc__
        self.code = code or self.__class__.__name__
        self.details = details or {}

    def to_dict(self):
        return {"error": self.code, "message": self.message, "details": self.details}


class ShopifyAuthException(ShopifyAppException):
    """Raised when authentication with Shopify fails."""

    pass


class ShopifyAPIException(ShopifyAppException):
    """Raised when a Shopify API call fails."""

    pass


class OpenAIException(ShopifyAppException):
    """Raised when an OpenAI API call fails."""

    pass


class DatabaseException(ShopifyAppException):
    """Raised for database-related errors."""

    pass


class ValidationException(ShopifyAppException):
    """Raised for validation errors in user input or data."""

    pass


class PermissionDeniedException(ShopifyAppException):
    """Raised when a user does not have permission to perform an action."""

    pass


class WebhookException(ShopifyAppException):
    """Raised for webhook processing errors."""

    pass


class CouponNotFoundError(ShopifyAppException):
    """Raised when a coupon with the given code is not found."""

    pass


class CouponExpiredError(ShopifyAppException):
    """Raised when a coupon has expired."""

    pass


class CouponAlreadyUsedError(ShopifyAppException):
    """Raised when a coupon has already been used."""

    pass


class InvalidCouponDataError(ValidationException):
    """Raised when provided coupon data is invalid."""

    pass


class InvalidHmacError(ShopifyAppException):
    """Raised when HMAC validation fails."""

    pass


class ShopifyDomainError(ShopifyAppException):
    """Raised for invalid Shopify domains."""

    pass
