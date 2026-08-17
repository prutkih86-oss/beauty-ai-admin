# data_access/settings.py
from database import get_connection


def get_all_settings() -> dict:
    # get app settings as key-value dictionary
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        rows = cursor.execute("SELECT key, value FROM settings").fetchall()
        return {r["key"]: r["value"] for r in rows}
    except Exception:
        # fallback if settings table is not created yet
        return {
            "business_name": "Beauty AI Salon",
            "support_email": "support@beautyai.com",
            "support_phone": "+380441112233",
            "currency": "USD",
            "timezone": "Europe/Kyiv",
        }
    finally:
        conn.close()


def save_setting(key: str, value: str) -> None:
    # insert or update a setting record
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )
        conn.commit()
    finally:
        conn.close()


def save_settings_batch(settings_dict: dict) -> None:
    # save multiple settings at once
    for key, val in settings_dict.items():
        save_setting(key, str(val))