from dataclasses import dataclass

from database import get_connection
from config import USE_BACKEND_API
from api_client import api_get


@dataclass
class ServiceRow:
    id: int | str
    name: str
    category: str
    duration_min: int
    price: float
    masters: str
    bookings: int


def _get_services_sql(search: str = "", category: str = "All") -> list[ServiceRow]:
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            s.service_id AS service_id,
            s.service_name AS name,
            s.category AS category,
            s.duration_min AS duration_min,
            s.base_price AS price
        FROM services s
        WHERE 1=1
    """
    params: list = []

    if search:
        query += " AND s.service_name LIKE ?"
        params.append(f"%{search}%")

    if category != "All":
        query += " AND s.category = ?"
        params.append(category)

    query += " ORDER BY s.service_name"

    services = cursor.execute(query, params).fetchall()

    rows = []
    for s in services:
        masters = cursor.execute(
            """
            SELECT DISTINCT m.master_name
            FROM bookings b
            JOIN masters m ON m.master_id = b.master_id
            WHERE b.service_id = ?
            LIMIT 3
            """,
            (s["service_id"],),
        ).fetchall()

        bookings_count = cursor.execute(
            "SELECT COUNT(*) AS total FROM bookings WHERE service_id = ?",
            (s["service_id"],),
        ).fetchone()["total"]

        rows.append(
            ServiceRow(
                id=s["service_id"],
                name=s["name"],
                category=s["category"],
                duration_min=s["duration_min"],
                price=s["price"],
                masters=", ".join(m["master_name"] for m in masters) or "—",
                bookings=bookings_count,
            )
        )

    conn.close()
    return rows


def _get_services_api(search: str = "", category: str = "All") -> list[ServiceRow]:
    # NOTE: /api/services/ is currently returning a 500 error on the backend
    # (FieldError: Cannot resolve keyword 'master_appointments' into field —
    # a bug in beauty_service/views.py). This will fail until that's fixed.
    # Response shape (from schema): id, name, description, category, price,
    # duration_minutes, salons[], masters[], image.
    data = api_get("/api/services/")
    results = data.get("results", data if isinstance(data, list) else [])

    rows = []
    for item in results:
        name = item.get("name", "")
        category_name = item.get("category", "")

        if search and search.lower() not in name.lower():
            continue
        if category != "All" and category_name != category:
            continue

        masters = item.get("masters", [])
        master_names = ", ".join(
            f"{m.get('first_name', '')} {m.get('last_name', '')}".strip() for m in masters[:3]
        )

        rows.append(
            ServiceRow(
                id=item.get("id"),
                name=name,
                category=category_name,
                duration_min=item.get("duration_minutes", 0),
                price=float(item.get("price", 0)),
                masters=master_names or "—",
                bookings=0,  # not available from this endpoint
            )
        )

    return rows


def get_services(search: str = "", category: str = "All") -> list[ServiceRow]:
    if USE_BACKEND_API:
        return _get_services_api(search, category)
    return _get_services_sql(search, category)


def _add_service_sql(name: str, category: str, duration: int, price: float) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO services (service_name, category, duration_min, base_price)
        VALUES (?, ?, ?, ?)
        """,
        (name.strip(), category, duration, price),
    )
    conn.commit()
    conn.close()


def _add_service_api(name: str, category: str, duration: int, price: float) -> None:
    # NOTE: no POST /api/services/ confirmed in the schema yet — this will
    # raise until backend adds it.
    raise NotImplementedError(
        "Creating a service via the API isn't supported yet — "
        "ask backend for a POST /api/services/ endpoint."
    )


def add_service(name: str, category: str, duration: int, price: float) -> None:
    if USE_BACKEND_API:
        _add_service_api(name, category, duration, price)
    else:
        _add_service_sql(name, category, duration, price)


def _update_service_sql(service_id: int, category: str, duration: int, price: float) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE services SET category = ?, duration_min = ?, base_price = ? WHERE service_id = ?",
        (category, duration, price, service_id),
    )
    conn.commit()
    conn.close()


def _update_service_api(service_id, category: str, duration: int, price: float) -> None:
    raise NotImplementedError(
        "Editing a service via the API isn't supported yet — "
        "ask backend for a PUT/PATCH /api/services/{id}/ endpoint."
    )


def update_service(service_id, category: str, duration: int, price: float) -> None:
    if USE_BACKEND_API:
        _update_service_api(service_id, category, duration, price)
    else:
        _update_service_sql(service_id, category, duration, price)


def _delete_service_sql(service_id: int) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM services WHERE service_id = ?", (service_id,))
    conn.commit()
    conn.close()


def _delete_service_api(service_id) -> None:
    raise NotImplementedError(
        "Deleting a service via the API isn't supported yet — "
        "ask backend for a DELETE /api/services/{id}/ endpoint."
    )


def delete_service(service_id) -> None:
    if USE_BACKEND_API:
        _delete_service_api(service_id)
    else:
        _delete_service_sql(service_id)