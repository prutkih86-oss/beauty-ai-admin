from dataclasses import dataclass
from datetime import datetime, timedelta

from database import get_connection
from config import USE_BACKEND_API


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
    # NOTE: no admin-wide GET /api/users/clients/ (or similar) endpoint
    # confirmed on the backend yet — only /api/users/me/ (self) exists.
    # This will raise until backend adds a real clients-list endpoint.
    raise NotImplementedError(
        "Admin Clients list endpoint isn't available on the backend API yet — "
        "waiting for backend to add GET /api/users/clients/ (or similar)."
    )


def get_clients(search: str = "", status: str = "All") -> list[ClientRow]:
    if USE_BACKEND_API:
        return _get_clients_api(search, status)
    return _get_clients_sql(search, status)