from dataclasses import dataclass

from database import get_connection
from config import USE_BACKEND_API
from api_client import api_get, api_post, api_delete


@dataclass
class PaymentRow:
    id: int | str
    client: str
    booking_id: int | str
    amount: float
    method: str
    date: str


def _get_payments_sql(search: str = "", method: str = "All", date: str = "") -> list[PaymentRow]:
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            p.payment_id AS id,
            c.client_name AS client,
            p.booking_id AS booking_id,
            p.amount AS amount,
            p.payment_method AS method,
            p.payment_date AS payment_date
        FROM payments p
        JOIN bookings b ON b.booking_id = p.booking_id
        JOIN clients c ON c.client_id = b.client_id
        WHERE 1=1
    """
    params: list = []

    if search:
        query += " AND (c.client_name LIKE ? OR CAST(p.booking_id AS TEXT) LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like])

    if method != "All":
        query += " AND p.payment_method = ?"
        params.append(method)

    if date:
        query += " AND DATE(p.payment_date) = ?"
        params.append(date)

    query += " ORDER BY p.payment_date DESC LIMIT 200"

    rows = cursor.execute(query, params).fetchall()
    conn.close()

    return [
        PaymentRow(
            id=r["id"],
            client=r["client"],
            booking_id=r["booking_id"],
            amount=r["amount"],
            method=r["method"],
            date=r["payment_date"][:10],
        )
        for r in rows
    ]


def _get_payments_api(search: str = "", method: str = "All", date: str = "") -> list[PaymentRow]:
    # NOTE: /api/payments/ response shape not yet confirmed against real
    # data (no auth to test with yet). Payment model has amount, currency,
    # payment_method, payment_status, payment_date, appointment_id — but no
    # client name directly, so we may need a nested client/appointment
    # object in the response, or a second lookup. Adjust field access below
    # once we see a real response.
    data = api_get("/api/payments/")
    results = data.get("results", data if isinstance(data, list) else [])

    rows = []
    for item in results:
        client = item.get("client_name") or item.get("client", "")
        payment_date = (item.get("payment_date") or "")[:10]

        if search and search.lower() not in str(client).lower() and search not in str(item.get("appointment_id", "")):
            continue
        if method != "All" and item.get("payment_method") != method:
            continue
        if date and payment_date != date:
            continue

        rows.append(
            PaymentRow(
                id=item.get("id"),
                client=client,
                booking_id=item.get("appointment_id") or item.get("appointment"),
                amount=float(item.get("amount", 0)),
                method=item.get("payment_method", ""),
                date=payment_date,
            )
        )

    return rows


def get_payments(search: str = "", method: str = "All", date: str = "") -> list[PaymentRow]:
    if USE_BACKEND_API:
        return _get_payments_api(search, method, date)
    return _get_payments_sql(search, method, date)


def _add_payment_sql(booking_id: int, amount: float, method: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO payments (booking_id, amount, payment_method, payment_date)
        VALUES (?, ?, ?, DATETIME('now'))
        """,
        (booking_id, amount, method),
    )
    conn.commit()
    conn.close()


def _add_payment_api(booking_id, amount: float, method: str) -> None:
    # NOTE: backend field is "appointment_id", and payment_status/currency
    # are also on the model — sending only these three may fail validation
    # until we confirm which fields are required vs have defaults.
    api_post(
        "/api/payments/",
        {"appointment_id": booking_id, "amount": amount, "payment_method": method},
    )


def add_payment(booking_id, amount: float, method: str) -> None:
    if USE_BACKEND_API:
        _add_payment_api(booking_id, amount, method)
    else:
        _add_payment_sql(booking_id, amount, method)


def _delete_payment_sql(payment_id: int) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM payments WHERE payment_id = ?", (payment_id,))
    conn.commit()
    conn.close()


def _delete_payment_api(payment_id) -> None:
    api_delete(f"/api/payments/{payment_id}/")


def delete_payment(payment_id) -> None:
    if USE_BACKEND_API:
        _delete_payment_api(payment_id)
    else:
        _delete_payment_sql(payment_id)