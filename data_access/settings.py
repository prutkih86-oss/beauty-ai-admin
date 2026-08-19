# data_access/settings.py

_DEFAULT_SETTINGS = {
    "business_name": "Beauty AI Salon",
    "support_email": "support@beautyai.com",
    "support_phone": "+380441112233",
    "currency": "USD",
    "timezone": "Europe/Kyiv",
    "admin_email": "admin@beautyai.com",
    "tfa_enabled": "False",
}

_runtime_settings = _DEFAULT_SETTINGS.copy()


def get_all_settings() -> dict:
    return _runtime_settings.copy()


def save_setting(key: str, value: str) -> None:
    _runtime_settings[key] = str(value)


def save_settings_batch(settings_dict: dict) -> None:
    for key, val in settings_dict.items():
        save_setting(key, str(val))