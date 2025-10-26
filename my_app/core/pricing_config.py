from typing import Dict, Any

# Define the pricing tiers and their features/limits
PRICING_PLANS: Dict[str, Dict[str, Any]] = {
    "free": {
        "name": "Free",
        "price": 0.0,
        "description": "Free tier with limited access.",
        "features": {
            "descriptions_generated_short": 100,  # First 100 free
            "descriptions_generated_long": 0,  # No free long descriptions
            "images_processed_sd": 0,  # Limited access, first month free
            "images_processed_hd": 0,  # Limited access, first month free
            "users": 1,
            "brand_voice_created": 1,
            "analytics_reports_generated": 0,
            "api_calls_made": 0,
            "storage_used_mb": 0,
        },
        "trial_days": 30,  # For other features
    },
    "basic": {
        "name": "Basic",
        "price": 10.00,
        "description": "Basic access to features.",
        "features": {
            "descriptions_generated_short": -1,  # Unlimited, but charged per usage
            "descriptions_generated_long": -1,  # Unlimited, but charged per usage
            "images_processed_sd": 20,  # 20% power
            "images_processed_hd": 5,  # 20% power
            "users": 2,
            "brand_voice_created": 2,
            "analytics_reports_generated": 5,
            "api_calls_made": 100,
            "storage_used_mb": 100,
        },
        "feature_access_percentage": 20,
        "power_user_threshold_descriptions": 500,  # New configurable threshold
    },
    "advanced": {
        "name": "Advanced",
        "price": 30.00,
        "description": "Advanced access to features.",
        "features": {
            "descriptions_generated_short": -1,  # Unlimited, but charged per usage
            "descriptions_generated_long": -1,  # Unlimited, but charged per usage
            "images_processed_sd": 50,  # 50% power
            "images_processed_hd": 15,  # 50% power
            "users": 5,
            "brand_voice_created": 5,
            "analytics_reports_generated": 15,
            "api_calls_made": 500,
            "storage_used_mb": 500,
        },
        "feature_access_percentage": 50,
    },
    "enterprise": {
        "name": "Enterprise",
        "price": 50.00,
        "description": "Unlimited access to all features.",
        "features": {
            "descriptions_generated_short": -1,  # Unlimited, but charged per usage
            "descriptions_generated_long": -1,  # Unlimited, but charged per usage
            "images_processed_sd": -1,  # Unlimited
            "images_processed_hd": -1,  # Unlimited
            "users": -1,
            "brand_voice_created": -1,
            "analytics_reports_generated": -1,
            "api_calls_made": -1,
            "storage_used_mb": -1,
        },
        "feature_access_percentage": 100,
    },
}

# Usage charge rates
USAGE_CHARGE_RATES: Dict[str, float] = {
    "descriptions_generated_short": 0.05,  # 5 cents per short description
    "descriptions_generated_long": 0.15,  # 15 cents per long description
}
