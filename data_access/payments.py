from dataclasses import dataclass

from api_client import api_delete, api_get, api_post
from config import USE_BACKEND_API
from database import get_connection


@dataclass
class PaymentRow:
    id: int | str
    client: str
    booking_id: int | str
    amount: float
    method: str
    date: str


def _get_payments_sql(
    search: str = "", method: str = "All", date: str = ""
) -> list[PaymentRow]:
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
            amount=float(r["amount"] or 0.0),
            method=r["method"],
            date=str(r["payment_date"])[:10] if r["payment_date"] else "—",
        )
        for r in rows
    ]


def _get_payments_api(
    search: str = "", method: str = "All", date: str = ""
) -> list[PaymentRow]:
    try:
        data = api_get("/api/payments/")
    except Exception as e:
        print(f"[API Payments Error]: {e}")
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

        payment_id = item.get("id", "N/A")

        # Обробка appointment (може бути dict або int/str)
        appointment = item.get("appointment") or item.get("appointment_id")
        if isinstance(appointment, dict):
            booking_id = appointment.get("id", "N/A")
            client = (
                appointment.get("client_name")
                or appointment.get("client")
                or item.get("client_name")
                or "N/A"
            )
        else:
            booking_id = appointment or "N/A"
            client = item.get("client_name") or item.get("client") or "N/A"

        # Дата платежу
        payment_date_raw = item.get("payment_date") or item.get("created_at") or item.get("date")
        payment_date = str(payment_date_raw)[:10] if payment_date_raw else "—"

        # Спосіб оплати та сума
        pay_method = str(item.get("payment_method") or item.get("method") or "Cash")
        try:
            amount = float(item.get("amount") or 0.0)
        except (ValueError, TypeError):
            amount = 0.0

        # Фільтрація
        if (
            search
            and search.lower() not in str(client).lower()
            and search not in str(booking_id)
            and search not in str(payment_id)
        ):
            continue

        if method != "All" and pay_method.lower() != method.lower():
            continue

        if date and payment_date != date:
            continue

        rows.append(
            PaymentRow(
                id=payment_id,
                client=str(client),
                booking_id=booking_id,
                amount=amount,
                method=pay_method,
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
    try:
        b_id = int(booking_id) if str(booking_id).isdigit() else booking_id
    except (ValueError, TypeError):
        b_id = booking_id

    payload = {
        "appointment": b_id,
        "amount": float(amount),
        "payment_method": method,
        "payment_status": "COMPLETED",
        "currency": "UAH",
    }
    try:
        api_post("/api/payments/", payload)
    except Exception as e:
        print(f"[API Add Payment Error]: {e}")


def add_payment(booking_id, amount: float, method: str) -> None:
    if USE_BACKEND_API:
        _add_payment_api(booking_id, amount, method)
    else:
        _add_payment_sql(int(booking_id), float(amount), method)


def _delete_payment_sql(payment_id: int) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM payments WHERE payment_id = ?", (payment_id,))
    conn.commit()
    conn.close()


def _delete_payment_api(payment_id) -> None:
    try:
        api_delete(f"/api/payments/{payment_id}/")
    except Exception as e:
        print(f"[API Delete Payment Error]: {e}")


def delete_payment(payment_id) -> None:
    if USE_BACKEND_API:
        _delete_payment_api(payment_id)
    else:
        _delete_payment_sql(int(payment_id))