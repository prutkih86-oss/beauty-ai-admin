from dataclasses import dataclass

from database import get_connection
from config import USE_BACKEND_API
from api_client import api_get, api_post


@dataclass
class MasterRow:
    name: str
    specialization: str
    rating: float
    city: str
    bookings: int
    revenue: float
    is_solo: bool


def _get_masters_sql(search: str = "", category: str = "All") -> list[MasterRow]:
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            m.master_name AS name,
            m.specialization AS specialization,
            m.rating_base AS rating,
            m.city AS city,
            m.is_solo AS is_solo,
            COUNT(DISTINCT b.booking_id) AS bookings,
            COALESCE(SUM(p.amount), 0) AS revenue
        FROM masters m
        LEFT JOIN bookings b ON b.master_id = m.master_id
        LEFT JOIN payments p ON p.booking_id = b.booking_id
        WHERE 1=1
    """
    params: list = []

    if search:
        query += " AND m.master_name LIKE ?"
        params.append(f"%{search}%")

    if category != "All":
        query += " AND m.specialization = ?"
        params.append(category)

    query += " GROUP BY m.master_id"

    rows = cursor.execute(query, params).fetchall()
    conn.close()

    return [
        MasterRow(
            name=r["name"],
            specialization=r["specialization"],
            rating=r["rating"],
            city=r["city"],
            bookings=r["bookings"],
            revenue=r["revenue"],
            is_solo=bool(r["is_solo"]),
        )
        for r in rows
    ]


def _get_masters_api(search: str = "", category: str = "All") -> list[MasterRow]:
    # NOTE: /api/users/masters currently has no search/category filter or
    # rating/bookings/revenue fields in its response (see MasterList schema:
    # id, first_name, last_name, photo, average_rating, years_of_experience,
    # salons[], services[]). Filtering by name/category is done client-side
    # here until the backend adds real query params. Revenue and per-master
    # bookings count aren't available from this endpoint at all yet.
    data = api_get("/api/users/masters")
    results = data.get("results", data if isinstance(data, list) else [])

    rows = []
    for item in results:
        name = f"{item.get('first_name', '')} {item.get('last_name', '')}".strip()
        specialization = item.get("specialization", "")  # not in current API response
        city = item.get("salons", [{}])[0].get("city", "") if item.get("salons") else ""

        if search and search.lower() not in name.lower():
            continue
        if category != "All" and specialization != category:
            continue

        rows.append(
            MasterRow(
                name=name,
                specialization=specialization,
                rating=item.get("average_rating") or 0,
                city=city,
                bookings=0,   # not available from this endpoint yet
                revenue=0,    # not available from this endpoint yet
                is_solo=not bool(item.get("salons")),
            )
        )

    return rows


def get_masters(search: str = "", category: str = "All") -> list[MasterRow]:
    if USE_BACKEND_API:
        return _get_masters_api(search, category)
    return _get_masters_sql(search, category)


def _add_master_sql(name: str, specialization: str, city: str, address: str, is_solo: bool) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO masters (master_name, specialization, city, address, is_solo, rating_base, hire_date)
        VALUES (?, ?, ?, ?, ?, ?, DATE('now'))
        """,
        (name.strip(), specialization, city.strip() or None, address.strip() or None, int(is_solo), 4.5),
    )
    conn.commit()
    conn.close()


def _add_master_api(name: str, specialization: str, city: str, address: str, is_solo: bool) -> None:
    # NOTE: there is currently no POST endpoint to create a master directly.
    # Backend confirmed (as of this writing) master creation only happens
    # via Django admin or direct DB access. This will raise until that
    # endpoint exists.
    raise NotImplementedError(
        "Creating a master via the API isn't supported yet — "
        "ask backend for a POST /api/users/masters/ endpoint."
    )


def add_master(name: str, specialization: str, city: str, address: str, is_solo: bool) -> None:
    if USE_BACKEND_API:
        _add_master_api(name, specialization, city, address, is_solo)
    else:
        _add_master_sql(name, specialization, city, address, is_solo)