from database import get_connection


def check_db() -> None:
    # simple connection test script
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        print("успішне підключення до postgresql!")
        print(f"версія бд: {db_version['version']}")
        conn.close()
    except Exception as e:
        print(f"помилка підключення: {e}")


if __name__ == "__main__":
    check_db()