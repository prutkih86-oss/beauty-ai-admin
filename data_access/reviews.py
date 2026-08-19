from dataclasses import dataclass

from api_client import api_delete, api_get
from config import USE_BACKEND_API
from database import get_connection


@dataclass
class ReviewRow:
    id: int | str
    client: str
    master: str
    service: str
    rating: int
    date: str


def _get_reviews_sql(search: str = "", rating: str = "All") -> list[ReviewRow]:
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            r.review_id AS id,
            c.client_name AS client,
            m.master_name AS master,
            s.service_name AS service,
            r.rating AS rating,
            r.review_date AS review_date
        FROM reviews r
        JOIN bookings b ON b.booking_id = r.booking_id
        JOIN clients c ON c.client_id = b.client_id
        JOIN masters m ON m.master_id = b.master_id
        JOIN services s ON s.service_id = b.service_id
        WHERE 1=1
    """
    params: list = []

    if search:
        query += " AND (c.client_name LIKE ? OR m.master_name LIKE ? OR s.service_name LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like, like])

    if rating != "All":
        query += " AND r.rating = ?"
        params.append(int(rating))

    query += " ORDER BY r.review_date DESC LIMIT 200"

    rows = cursor.execute(query, params).fetchall()
    conn.close()

    return [
        ReviewRow(
            id=r["id"],
            client=r["client"],
            master=r["master"],
            service=r["service"],
            rating=int(r["rating"] or 0),
            date=str(r["review_date"])[:10] if r["review_date"] else "—",
        )
        for r in rows
    ]


def _get_reviews_api(search: str = "", rating: str = "All") -> list[ReviewRow]:
    try:
        data = api_get("/api/reviews/")
    except Exception as e:
        print(f"[API Reviews Error]: {e}")
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

        review_id = item.get("id", "N/A")

        # Парсинг імені клієнта (вкладений dict або строка)
        client_data = item.get("client") or item.get("user") or item.get("author")
        if isinstance(client_data, dict):
            first = client_data.get("first_name", "")
            last = client_data.get("last_name", "")
            client = f"{first} {last}".strip() or client_data.get("email") or "N/A"
        else:
            client = item.get("client_name") or (str(client_data) if client_data else "N/A")

        # Парсинг імені майстра
        master_data = item.get("master")
        if isinstance(master_data, dict):
            first = master_data.get("first_name", "")
            last = master_data.get("last_name", "")
            master = f"{first} {last}".strip() or master_data.get("email") or "N/A"
        else:
            master = item.get("master_name") or (str(master_data) if master_data else "N/A")

        # Парсинг назви послуги
        appointment_data = item.get("appointment") or item.get("booking")
        if isinstance(appointment_data, dict):
            service_obj = appointment_data.get("service") or appointment_data.get("service_name")
            if isinstance(service_obj, dict):
                service = service_obj.get("name") or service_obj.get("service_name") or "N/A"
            else:
                service = str(service_obj) if service_obj else "N/A"
        else:
            service = item.get("service_name") or item.get("service") or "N/A"

        # Оцінка
        try:
            review_rating = int(item.get("rating") or item.get("stars") or 0)
        except (ValueError, TypeError):
            review_rating = 0

        # Дата
        date_raw = item.get("created_at") or item.get("review_date") or item.get("date")
        date = str(date_raw)[:10] if date_raw else "—"

        # Фільтрація
        if search and search.lower() not in f"{client} {master} {service}".lower():
            continue

        if rating != "All":
            try:
                if review_rating != int(rating):
                    continue
            except (ValueError, TypeError):
                continue

        rows.append(
            ReviewRow(
                id=review_id,
                client=client,
                master=master,
                service=str(service),
                rating=review_rating,
                date=date,
            )
        )

    return rows


def get_reviews(search: str = "", rating: str = "All") -> list[ReviewRow]:
    if USE_BACKEND_API:
        return _get_reviews_api(search, rating)
    return _get_reviews_sql(search, rating)


def _delete_review_sql(review_id: int) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reviews WHERE review_id = ?", (review_id,))
    conn.commit()
    conn.close()


def _delete_review_api(review_id) -> None:
    try:
        api_delete(f"/api/reviews/{review_id}/")
    except Exception as e:
        print(f"[API Delete Review Error]: {e}")


def delete_review(review_id) -> None:
    if USE_BACKEND_API:
        _delete_review_api(review_id)
    else:
        _delete_review_sql(int(review_id))