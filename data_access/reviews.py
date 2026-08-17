from dataclasses import dataclass

from database import get_connection
from config import USE_BACKEND_API
from api_client import api_get


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
            rating=r["rating"],
            date=r["review_date"][:10],
        )
        for r in rows
    ]


def _get_reviews_api(search: str = "", rating: str = "All") -> list[ReviewRow]:
    # NOTE: backend reviews model has rating, comment, created_at,
    # appointment_id, client_id, master_id — no nested client/master/service
    # names confirmed yet, so this may need extra lookups or a richer
    # serializer once we can actually test against the real API.
    data = api_get("/api/reviews/")
    results = data.get("results", data if isinstance(data, list) else [])

    rows = []
    for item in results:
        client = item.get("client_name", "")
        master = item.get("master_name", "")
        service = item.get("service_name", "")
        review_rating = item.get("rating", 0)
        date = (item.get("created_at") or "")[:10]

        if search and search.lower() not in f"{client} {master} {service}".lower():
            continue
        if rating != "All" and str(review_rating) != rating:
            continue

        rows.append(
            ReviewRow(
                id=item.get("id"),
                client=client,
                master=master,
                service=service,
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
    # NOTE: no DELETE /api/reviews/{id}/ confirmed in the schema yet —
    # this will raise until backend adds it.
    raise NotImplementedError(
        "Deleting a review via the API isn't supported yet — "
        "ask backend for a DELETE /api/reviews/{id}/ endpoint."
    )


def delete_review(review_id) -> None:
    if USE_BACKEND_API:
        _delete_review_api(review_id)
    else:
        _delete_review_sql(review_id)