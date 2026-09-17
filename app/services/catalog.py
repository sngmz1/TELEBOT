SERVICES = {
    "info_gathering": {
        "name": "🔎 Information Gathering",
        "description": "We collect and compile information from publicly available sources.",
        "info_types": [
            {"key": "telegram_id", "type": "Telegram ID", "prompt": "Enter the Telegram ID or username:", "example": "123456789 or @username"},
            {"key": "mobile", "type": "Mobile Number", "prompt": "Enter the Mobile Number:", "example": "9876543210"},
            {"key": "email", "type": "Email ID", "prompt": "Enter the Email ID:", "example": "name@example.com"},
        ],
        "packages": {
            "basic": {"name": "Basic", "price": "₹159", "max_info": 1, "time": "24 hours"},
            "standard": {"name": "Standard", "price": "₹449", "max_info": 4, "time": "12 hours"},
            "premium": {"name": "Premium", "price": "₹949", "max_info": 10, "time": "6 hours"},
        },
    },
}

BLOCKED_INFO_TYPES = [
    "password", "otp", "pin", "cvv", "banking", "card",
    "bank login", "net banking", "upi pin", "atm pin",
]