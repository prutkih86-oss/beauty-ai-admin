from dataclasses import dataclass

from database import get_connection
from config import USE_BACKEND_API
from api_client import api_get, api_post, api_put, api_delete


@dataclass
class SalonRow:
    id: int | str
    name: str
    city: str
    address: str
    popularity_score: float


def _get_salons_sql(search: str = "") -> list[SalonRow]:
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT salon_id, salon_name, city, address, popularity_score
        FROM salons
        WHERE 1=1
    """
    params: list = []

    if search:
        query += " AND (salon_name LIKE ? OR city LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like])

    query += " ORDER BY city, salon_name"

    rows = cursor.execute(query, params).fetchall()
    conn.close()

    return [
        SalonRow(
            id=r["salon_id"],
            name=r["salon_name"],
            city=r["city"],
            address=r["address"] or "",
            popularity_score=r["popularity_score"],
        )
        for r in rows
    ]


def _get_salons_api(search: str = "") -> list[SalonRow]:
    # NOTE: verify the real query param name for search once we have API
    # access (schema didn't show one explicitly for /api/salons/ — may need
    # to filter client-side like we do for masters, same as here for now).
    data = api_get("/api/salons/")
    results = data.get("results", data if isinstance(data, list) else [])

    rows = []
    for item in results:
        name = item.get("name", "")
        city = item.get("city", "")

        if search and search.lower() not in name.lower() and search.lower() not in city.lower():
            continue

        rows.append(
            SalonRow(
                id=item.get("id"),
                name=name,
                city=city,
                address=item.get("address", ""),
                popularity_score=0,  # not part of the backend salon model
            )
        )

    return rows


def get_salons(search: str = "") -> list[SalonRow]:
    if USE_BACKEND_API:
        return _get_salons_api(search)
    return _get_salons_sql(search)


def _add_salon_sql(name: str, city: str, address: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO salons (salon_name, city, address, opened_date, popularity_score)
        VALUES (?, ?, ?, DATE('now'), ?)
        """,
        (name.strip(), city.strip() or None, address.strip() or None, 4.0),
    )
    conn.commit()
    conn.close()


def _add_salon_api(name: str, city: str, address: str) -> None:
    # NOTE: the backend Salon model requires more fields than we collect in
    # our simple form (phone, latitude/longitude, logo, available_status,
    # salon_status are all present in their schema). Sending only
    # name/city/address will likely fail validation until we either extend
    # the form or confirm which of those fields are actually required vs
    # optional on their side.
    api_post(
        "/api/salons/",
        {"name": name.strip(), "city": city.strip(), "address": address.strip()},
    )


def add_salon(name: str, city: str, address: str) -> None:
    if USE_BACKEND_API:
        _add_salon_api(name, city, address)
    else:
        _add_salon_sql(name, city, address)


def _update_salon_sql(salon_id: int, city: str, address: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE salons SET city = ?, address = ? WHERE salon_id = ?",
        (city.strip() or None, address.strip() or None, salon_id),
    )
    conn.commit()
    conn.close()


def _update_salon_api(salon_id, city: str, address: str) -> None:
    api_put(f"/api/salons/{salon_id}/", {"city": city.strip(), "address": address.strip()})


def update_salon(salon_id, city: str, address: str) -> None:
    if USE_BACKEND_API:
        _update_salon_api(salon_id, city, address)
    else:
        _update_salon_sql(salon_id, city, address)


def _delete_salon_sql(salon_id: int) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM salons WHERE salon_id = ?", (salon_id,))
    conn.commit()
    conn.close()


def _delete_salon_api(salon_id) -> None:
    api_delete(f"/api/salons/{salon_id}/")


def delete_salon(salon_id) -> None:
    if USE_BACKEND_API:
        _delete_salon_api(salon_id)
    else:
        _delete_salon_sql(salon_id)