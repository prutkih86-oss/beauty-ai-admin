from dataclasses import dataclass
from api_client import api_get, api_post
from config import USE_BACKEND_API
from database import get_connection


@dataclass
class MasterRow:
    name: str
    specialization: str
    rating: float
    city: str
    bookings: int
    revenue: float
    is_solo: bool


def _get_masters_sql(search: str = "", category: str = "All") -> list[MasterRow]:
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            m.master_name AS name,
            m.specialization AS specialization,
            m.rating_base AS rating,
            m.city AS city,
            m.is_solo AS is_solo,
            COUNT(DISTINCT b.booking_id) AS bookings,
            COALESCE(SUM(p.amount), 0) AS revenue
        FROM masters m
        LEFT JOIN bookings b ON b.master_id = m.master_id
        LEFT JOIN payments p ON p.booking_id = b.booking_id
        WHERE 1=1
    """
    params: list = []

    if search:
        query += " AND m.master_name LIKE ?"
        params.append(f"%{search}%")

    if category != "All":
        query += " AND m.specialization = ?"
        params.append(category)

    query += " GROUP BY m.master_id"

    rows = cursor.execute(query, params).fetchall()
    conn.close()

    return [
        MasterRow(
            name=r["name"],
            specialization=r["specialization"],
            rating=r["rating"],
            city=r["city"],
            bookings=r["bookings"],
            revenue=r["revenue"],
            is_solo=bool(r["is_solo"]),
        )
        for r in rows
    ]


def _get_masters_api(search: str = "", category: str = "All") -> list[MasterRow]:
    try:
        # Відправляємо запит до підтвердженого ендпоінту
        data = api_get("/api/users/masters/")
    except Exception as e:
        print(f"[API Masters Error]: {e}")
        return []

    if isinstance(data, dict):
        results = data.get("results", [])
    elif isinstance(data, list):
        results = data
    else:
        results = []

    rows = []
    for item in results:
        if not isinstance(item, dict):
            continue

        first_name = item.get("first_name") or ""
        last_name = item.get("last_name") or ""
        name = f"{first_name} {last_name}".strip() or item.get("email") or "Unknown Master"

        # Визначаємо спеціалізацію: з прямого поля або беремо категорію першої послуги
        specialization = item.get("specialization") or ""
        if not specialization and item.get("services"):
            services = item.get("services", [])
            if services and isinstance(services[0], dict):
                specialization = services[0].get("category") or services[0].get("name") or "General"

        if not specialization:
            specialization = "General"

        # Отримання міста із салонів
        salons = item.get("salons", [])
        city = "N/A"
        if salons and isinstance(salons, list) and isinstance(salons[0], dict):
            city = salons[0].get("city") or salons[0].get("address") or "N/A"

        # Оцінка
        try:
            rating = float(item.get("average_rating") or item.get("rating") or 0.0)
        except (ValueError, TypeError):
            rating = 0.0

        # Фільтрація клієнтською частиною
        if search and search.lower() not in name.lower():
            continue
        if category != "All" and category.lower() not in specialization.lower():
            continue

        rows.append(
            MasterRow(
                name=name,
                specialization=specialization,
                rating=rating,
                city=city,
                bookings=int(item.get("bookings_count") or 0),
                revenue=float(item.get("total_revenue") or 0.0),
                is_solo=not bool(salons),
            )
        )

    return rows


def get_masters(search: str = "", category: str = "All") -> list[MasterRow]:
    if USE_BACKEND_API:
        return _get_masters_api(search, category)
    return _get_masters_sql(search, category)


def _add_master_sql(name: str, specialization: str, city: str, address: str, is_solo: bool) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO masters (master_name, specialization, city, address, is_solo, rating_base, hire_date)
        VALUES (?, ?, ?, ?, ?, ?, DATE('now'))
        """,
        (name.strip(), specialization, city.strip() or None, address.strip() or None, int(is_solo), 4.5),
    )
    conn.commit()
    conn.close()


def _add_master_api(name: str, specialization: str, city: str, address: str, is_solo: bool) -> None:
    parts = name.strip().split(" ", 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ""

    payload = {
        "first_name": first_name,
        "last_name": last_name,
        "specialization": specialization,
        "city": city,
        "address": address,
        "is_solo": is_solo,
    }

    try:
        api_post("/api/users/masters/", payload)
    except Exception as e:
        print(f"[API Add Master Error]: {e}")


def add_master(name: str, specialization: str, city: str, address: str, is_solo: bool) -> None:
    if USE_BACKEND_API:
        _add_master_api(name, specialization, city, address, is_solo)
    else:
        _add_master_sql(name, specialization, city, address, is_solo)