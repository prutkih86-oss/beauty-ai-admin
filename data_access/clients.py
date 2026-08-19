from dataclasses import dataclass
from datetime import datetime, timedelta

from api_client import api_get
from config import USE_BACKEND_API
from database import get_connection


@dataclass
class ClientRow:
    id: int | str
    name: str
    city: str
    acquisition_channel: str
    bookings: int
    spent: float
    last_visit: str
    status: str


def _get_clients_sql(search: str = "", status: str = "All") -> list[ClientRow]:
    conn = get_connection()
    cursor = conn.cursor()

    latest_row = cursor.execute(
        "SELECT MAX(booking_datetime) AS latest FROM bookings"
    ).fetchone()
    anchor_date = (
        datetime.fromisoformat(latest_row["latest"])
        if latest_row and latest_row["latest"]
        else datetime.now()
    )
    active_cutoff = (anchor_date - timedelta(days=90)).strftime("%Y-%m-%d")

    query = """
        SELECT
            c.client_id AS id,
            c.client_name AS name,
            c.city AS city,
            c.acquisition_channel AS acquisition_channel,
            COUNT(DISTINCT b.booking_id) AS bookings,
            COALESCE(SUM(p.amount), 0) AS spent,
            MAX(b.booking_datetime) AS last_visit
        FROM clients c
        LEFT JOIN bookings b ON b.client_id = c.client_id
        LEFT JOIN payments p ON p.booking_id = b.booking_id
        WHERE 1=1
    """
    params: list = []

    if search:
        query += " AND c.client_name LIKE ?"
        params.append(f"%{search}%")

    query += " GROUP BY c.client_id"

    rows_raw = cursor.execute(query, params).fetchall()
    conn.close()

    rows = []
    for r in rows_raw:
        last_visit = r["last_visit"]
        is_active = bool(last_visit and last_visit >= active_cutoff)
        client_status = "Active" if is_active else "Inactive"

        if status != "All" and client_status != status:
            continue

        rows.append(
            ClientRow(
                id=r["id"],
                name=r["name"],
                city=r["city"],
                acquisition_channel=r["acquisition_channel"],
                bookings=r["bookings"],
                spent=r["spent"],
                last_visit=last_visit[:10] if last_visit else "—",
                status=client_status,
            )
        )

    return rows


def _get_clients_api(search: str = "", status: str = "All") -> list[ClientRow]:
    params = {}
    if search:
        params["search"] = search

    try:
        data = api_get("/api/users/clients/", params=params)
    except Exception as e:
        print(f"[API Clients Error]: {e}")
        return []

    # Обробка пагінованої відповіді Джанго або чистого списку
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

        client_id = item.get("id", "N/A")

        # Формування імені клієнта
        first_name = item.get("first_name") or ""
        last_name = item.get("last_name") or ""
        full_name = (
            f"{first_name} {last_name}".strip()
            or item.get("client_name")
            or item.get("name")
            or item.get("email")
            or f"Client #{client_id}"
        )

        # Отримання міста
        city_data = item.get("city") or item.get("location")
        if isinstance(city_data, dict):
            city_name = city_data.get("city_name") or city_data.get("name") or "N/A"
        else:
            city_name = str(city_data) if city_data else "N/A"

        acquisition = item.get("acquisition_channel") or item.get("source") or "Direct"

        # Безпечне приведення чисел
        try:
            bookings_cnt = int(item.get("bookings_count") or item.get("total_bookings") or 0)
        except (ValueError, TypeError):
            bookings_cnt = 0

        try:
            spent_amt = float(item.get("total_spent") or item.get("spent") or 0.0)
        except (ValueError, TypeError):
            spent_amt = 0.0

        # Форматування дати останнього візиту
        last_visit_raw = item.get("last_visit") or item.get("last_booking_date")
        last_visit = str(last_visit_raw)[:10] if last_visit_raw else "—"

        # Визначення статусу
        is_active = item.get("is_active", True)
        client_status = "Active" if is_active else "Inactive"

        if status != "All" and client_status != status:
            continue

        rows.append(
            ClientRow(
                id=client_id,
                name=full_name,
                city=city_name,
                acquisition_channel=acquisition,
                bookings=bookings_cnt,
                spent=spent_amt,
                last_visit=last_visit,
                status=client_status,
            )
        )

    return rows


def get_clients(search: str = "", status: str = "All") -> list[ClientRow]:
    if USE_BACKEND_API:
        return _get_clients_api(search, status)
    return _get_clients_sql(search, status)