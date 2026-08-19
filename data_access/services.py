from dataclasses import dataclass

from api_client import api_get
from config import USE_BACKEND_API
from database import get_connection


@dataclass
class ServiceRow:
    id: int | str
    name: str
    category: str
    duration: int
    price: float
    masters: str
    bookings: int


def _get_services_sql(
    search: str = "",
    category: str = "All"
) -> list[ServiceRow]:
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            s.service_id AS id,
            s.service_name AS name,
            s.category AS category,
            s.duration_min AS duration,
            s.base_price AS price
        FROM services s
        WHERE 1=1
    """

    params = []

    if search:
        query += " AND s.service_name LIKE ?"
        params.append(f"%{search}%")

    if category != "All":
        query += " AND s.category = ?"
        params.append(category)

    query += " ORDER BY s.service_name"

    services = cursor.execute(query, params).fetchall()

    rows = []

    for service in services:
        masters = cursor.execute(
            """
            SELECT DISTINCT m.master_name
            FROM bookings b
            JOIN masters m ON m.master_id = b.master_id
            WHERE b.service_id = ?
            LIMIT 3
            """,
            (service["id"],),
        ).fetchall()

        bookings_count = cursor.execute(
            "SELECT COUNT(*) AS total FROM bookings WHERE service_id = ?",
            (service["id"],),
        ).fetchone()["total"]

        rows.append(
            ServiceRow(
                id=service["id"],
                name=service["name"],
                category=service["category"],
                duration=int(service["duration"] or 0),
                price=float(service["price"] or 0),
                masters=", ".join(m["master_name"] for m in masters) or "—",
                bookings=int(bookings_count or 0),
            )
        )

    conn.close()
    return rows


def _get_services_api(
    search: str = "",
    category: str = "All"
) -> list[ServiceRow]:

    params = {}

    if search:
        params["service_name"] = search

    if category != "All":
        params["category"] = category

    try:
        data = api_get("/api/services/", params=params)
    except Exception as e:
        print(f"[API Services Error]: {e}")
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

        masters_data = item.get("masters")

        if isinstance(masters_data, list):
            master_names = []

            for master in masters_data:
                if isinstance(master, dict):
                    master_names.append(
                        master.get("name")
                        or master.get("full_name")
                        or str(master.get("id", ""))
                    )
                else:
                    master_names.append(str(master))

            masters = ", ".join(master_names) or "—"

        elif masters_data:
            masters = str(masters_data)

        else:
            masters = "—"

        try:
            duration = int(item.get("duration_minutes") or 0)
        except (ValueError, TypeError):
            duration = 0

        try:
            price = float(item.get("price") or 0.0)
        except (ValueError, TypeError):
            price = 0.0

        rows.append(
            ServiceRow(
                id=item.get("id", "N/A"),
                name=item.get("name") or "Unknown Service",
                category=item.get("category") or "—",
                duration=duration,
                price=price,
                masters=masters,
                bookings=0,
            )
        )

    return rows


def get_services(
    search: str = "",
    category: str = "All"
) -> list[ServiceRow]:

    if USE_BACKEND_API:
        return _get_services_api(search, category)

    return _get_services_sql(search, category)