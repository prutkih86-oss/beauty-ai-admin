from dataclasses import dataclass

from database import get_connection
from config import USE_BACKEND_API
from api_client import api_get


@dataclass
class BookingRow:
    id: int | str
    client_name: str
    master_name: str
    service_name: str
    salon_name: str
    date_time: str
    status: str
    price: float


def _get_bookings_sql(search: str = "", status: str = "All") -> list[BookingRow]:
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            b.booking_id AS id,
            COALESCE(c.client_name, '—') AS client_name,
            COALESCE(m.master_name, '—') AS master_name,
            COALESCE(s.service_name, '—') AS service_name,
            COALESCE(sa.salon_name, '—') AS salon_name,
            b.booking_time AS date_time,
            b.status AS status,
            COALESCE(s.base_price, 0.0) AS price
        FROM bookings b
        LEFT JOIN clients c ON b.client_id = c.client_id
        LEFT JOIN masters m ON b.master_id = m.master_id
        LEFT JOIN services s ON b.service_id = s.service_id
        LEFT JOIN salons sa ON m.salon_id = sa.salon_id
        WHERE 1=1
    """

    params: list = []

    if search:
        query += """ AND (
            c.client_name LIKE ? OR
            m.master_name LIKE ? OR
            s.service_name LIKE ?
        )"""
        params.extend([
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
        ])

    if status != "All":
        query += " AND b.status = ?"
        params.append(status)

    query += " ORDER BY b.booking_time DESC"

    rows = cursor.execute(query, params).fetchall()
    conn.close()

    return [
        BookingRow(
            id=r["id"],
            client_name=r["client_name"],
            master_name=r["master_name"],
            service_name=r["service_name"],
            salon_name=r["salon_name"],
            date_time=str(r["date_time"]),
            status=r["status"] or "Pending",
            price=float(r["price"]),
        )
        for r in rows
    ]


def _get_bookings_api(
    search: str = "",
    status: str = "All"
) -> list[BookingRow]:

    try:
        data = api_get("/api/appointments/")
        
    except Exception as e:
        print(f"[API Bookings Error]: {e}")
        return []

    # Django pagination або звичайний список
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

        booking_id = (
            item.get("id")
            or item.get("appointment_id")
            or "N/A"
        )

        client_name = item.get("client_name") or "—"
        master_name = item.get("master_name") or "—"
        service_name = item.get("service_name") or "—"
        salon_name = item.get("salon_name") or "—"

        booking_status = (
            item.get("appointment_status")
            or item.get("status")
            or "Pending"
        )

        appointment_date = item.get("appointment_date") or ""
        appointment_time = item.get("appointment_time") or ""

        date_time = (
            f"{appointment_date} {appointment_time}".strip()
            or "—"
        )

        try:
            price = float(
                item.get("total_price")
                or item.get("price")
                or 0.0
            )
        except (ValueError, TypeError):
            price = 0.0

        # Пошук локально
        if search:
            search_lower = search.lower()

            if (
                search_lower not in client_name.lower()
                and search_lower not in master_name.lower()
                and search_lower not in service_name.lower()
            ):
                continue

        # Фільтр статусу
        if status != "All" and booking_status != status:
            continue

        rows.append(
            BookingRow(
                id=booking_id,
                client_name=client_name,
                master_name=master_name,
                service_name=service_name,
                salon_name=salon_name,
                date_time=date_time,
                status=booking_status,
                price=price,
            )
        )

    return rows


def get_bookings(
    search: str = "",
    status: str = "All"
) -> list[BookingRow]:

    if USE_BACKEND_API:
        return _get_bookings_api(search, status)

    return _get_bookings_sql(search, status)


def _update_booking_status_sql(
    booking_id: int | str,
    new_status: str
) -> None:

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE bookings SET status = ? WHERE booking_id = ?",
        (new_status, booking_id),
    )

    conn.commit()
    conn.close()


def _update_booking_status_api(
    booking_id: int | str,
    new_status: str
) -> None:

    raise NotImplementedError(
        "Updating booking status via API isn't supported yet."
    )


def update_booking_status(
    booking_id: int | str,
    new_status: str
) -> None:

    if USE_BACKEND_API:
        _update_booking_status_api(booking_id, new_status)
    else:
        _update_booking_status_sql(booking_id, new_status)


def _delete_booking_sql(
    booking_id: int | str
) -> None:

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM bookings WHERE booking_id = ?",
        (booking_id,)
    )

    conn.commit()
    conn.close()


def _delete_booking_api(
    booking_id: int | str
) -> None:

    raise NotImplementedError(
        "Deleting booking via API isn't supported yet."
    )


def delete_booking(
    booking_id: int | str
) -> None:

    if USE_BACKEND_API:
        _delete_booking_api(booking_id)
    else:
        _delete_booking_sql(booking_id)