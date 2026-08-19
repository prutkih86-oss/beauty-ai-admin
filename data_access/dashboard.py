from dataclasses import dataclass
from datetime import datetime, timedelta

from api_client import api_get


@dataclass
class DashboardBooking:
    id: int | str
    client: str
    master: str
    service: str
    date_time: str
    status: str
    price: float


@dataclass
class DashboardMaster:
    name: str
    rating: float
    bookings: int
    revenue: float


@dataclass
class DashboardData:
    anchor_date: datetime

    revenue_current: float
    revenue_previous: float

    bookings_current: int
    bookings_previous: int

    clients_current: int
    clients_previous: int

    masters_current: int
    masters_previous: int

    bookings_today: int
    completed_today: int
    cancelled_today: int
    noshow_today: int

    recent_bookings: list[DashboardBooking]
    today_schedule: list[DashboardBooking]
    top_masters: list[DashboardMaster]

    new_reviews_today: int
    low_ratings_today: int
    ai_searches_today: int


def _safe_datetime(value) -> datetime | None:
    if not value:
        return None

    text = str(value).strip()

    try:
        return datetime.fromisoformat(
            text.replace("Z", "+00:00")
        ).replace(tzinfo=None)
    except (ValueError, TypeError):
        pass

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    return None


def _safe_float(value) -> float:
    try:
        return float(value or 0)
    except (ValueError, TypeError):
        return 0.0


def _get_all_pages(
    path: str,
    params: dict | None = None,
    max_pages: int = 100,
) -> list[dict]:

    params = dict(params or {})
    results: list[dict] = []

    for page in range(1, max_pages + 1):
        page_params = dict(params)
        page_params["page"] = page

        data = api_get(path, params=page_params)

        if isinstance(data, list):
            results.extend(
                item for item in data
                if isinstance(item, dict)
            )
            break

        if not isinstance(data, dict):
            break

        page_results = data.get("results", [])

        if isinstance(page_results, list):
            results.extend(
                item for item in page_results
                if isinstance(item, dict)
            )

        if not data.get("next"):
            break

    return results


def _load_appointments() -> list[DashboardBooking]:
    try:
        items = _get_all_pages("/api/appointments/")
    except Exception as e:
        print(f"[Dashboard Appointments Error]: {e}")
        return []

    rows = []

    for item in items:
        date = item.get("appointment_date") or ""
        time = item.get("appointment_time") or ""

        date_time = f"{date} {time}".strip()

        rows.append(
            DashboardBooking(
                id=item.get("id")
                or item.get("appointment_id")
                or "N/A",

                client=item.get("client_name") or "—",
                master=item.get("master_name") or "—",
                service=item.get("service_name") or "—",

                date_time=date_time,

                status=(
                    item.get("appointment_status")
                    or item.get("status")
                    or "Pending"
                ),

                price=_safe_float(
                    item.get("total_price")
                    or item.get("price")
                ),
            )
        )

    return rows


def _load_clients() -> list[dict]:
    try:
        return _get_all_pages("/api/users/clients/")
    except Exception as e:
        print(f"[Dashboard Clients Error]: {e}")
        return []


def _load_masters() -> list[dict]:
    try:
        return _get_all_pages("/api/users/masters/")
    except Exception as e:
        print(f"[Dashboard Masters Error]: {e}")
        return []


def get_dashboard_data() -> DashboardData:

    bookings = _load_appointments()
    clients = _load_clients()
    masters_raw = _load_masters()

    parsed_bookings = []

    for booking in bookings:
        dt = _safe_datetime(booking.date_time)

        if dt:
            parsed_bookings.append((booking, dt))

    # Як у старій версії:
    # якщо bookings є — "сьогодні" = найновіший booking.
    # Якщо сервер порожній — використовуємо реальну дату.
    if parsed_bookings:
        anchor_date = max(
            dt for _, dt in parsed_bookings
        )
    else:
        anchor_date = datetime.now()

    current_start = anchor_date - timedelta(days=29)

    previous_end = current_start - timedelta(seconds=1)
    previous_start = previous_end - timedelta(days=29)

    def in_current(dt: datetime) -> bool:
        return current_start <= dt <= anchor_date

    def in_previous(dt: datetime) -> bool:
        return previous_start <= dt <= previous_end

    current_bookings = [
        booking
        for booking, dt in parsed_bookings
        if in_current(dt)
    ]

    previous_bookings = [
        booking
        for booking, dt in parsed_bookings
        if in_previous(dt)
    ]

    revenue_current = sum(
        booking.price
        for booking in current_bookings
    )

    revenue_previous = sum(
        booking.price
        for booking in previous_bookings
    )

    # --------------------------------
    # Clients registered in periods
    # --------------------------------

    clients_current = 0
    clients_previous = 0

    for client in clients:

        joined_raw = (
            client.get("date_joined")
            or client.get("registration_date_user")
        )

        joined = _safe_datetime(joined_raw)

        if not joined:
            continue

        if in_current(joined):
            clients_current += 1

        elif in_previous(joined):
            clients_previous += 1

    # --------------------------------
    # Active masters by appointments
    # --------------------------------

    current_master_names = {
        booking.master
        for booking in current_bookings
        if booking.master and booking.master != "—"
    }

    previous_master_names = {
        booking.master
        for booking in previous_bookings
        if booking.master and booking.master != "—"
    }

    masters_current = len(current_master_names)
    masters_previous = len(previous_master_names)

    # --------------------------------
    # Today
    # --------------------------------

    today_str = anchor_date.strftime("%Y-%m-%d")

    today_pairs = [
        (booking, dt)
        for booking, dt in parsed_bookings
        if dt.strftime("%Y-%m-%d") == today_str
    ]

    today_bookings = [
        booking
        for booking, _ in today_pairs
    ]

    def status_is(
        booking: DashboardBooking,
        target: str
    ) -> bool:
        return booking.status.lower() == target.lower()

    completed_today = sum(
        1 for b in today_bookings
        if status_is(b, "Completed")
    )

    cancelled_today = sum(
        1 for b in today_bookings
        if status_is(b, "Cancelled")
    )

    noshow_today = sum(
        1 for b in today_bookings
        if b.status.lower() in {
            "no-show",
            "no show",
            "noshow",
        }
    )

    # --------------------------------
    # Recent bookings
    # --------------------------------

    recent_bookings = [
        booking
        for booking, _ in sorted(
            parsed_bookings,
            key=lambda pair: pair[1],
            reverse=True,
        )[:30]
    ]

    # --------------------------------
    # Today's schedule
    # --------------------------------

    today_schedule = [
        booking
        for booking, _ in sorted(
            today_pairs,
            key=lambda pair: pair[1],
        )
    ]

    # --------------------------------
    # Master ratings
    # --------------------------------

    ratings: dict[str, float] = {}

    for item in masters_raw:

        first_name = item.get("first_name") or ""
        last_name = item.get("last_name") or ""

        name = (
            f"{first_name} {last_name}".strip()
            or item.get("name")
            or item.get("email")
            or ""
        )

        if not name:
            continue

        ratings[name] = _safe_float(
            item.get("average_rating")
            or item.get("rating")
        )

    # --------------------------------
    # Top masters today
    # --------------------------------

    master_stats: dict[str, dict] = {}

    for booking in today_bookings:

        name = booking.master

        if not name or name == "—":
            continue

        if name not in master_stats:
            master_stats[name] = {
                "bookings": 0,
                "revenue": 0.0,
            }

        master_stats[name]["bookings"] += 1
        master_stats[name]["revenue"] += booking.price

    top_masters = []

    for name, stats in master_stats.items():

        top_masters.append(
            DashboardMaster(
                name=name,
                rating=ratings.get(name, 0.0),
                bookings=stats["bookings"],
                revenue=stats["revenue"],
            )
        )

    top_masters.sort(
        key=lambda m: (
            m.bookings,
            m.rating,
            m.revenue,
        ),
        reverse=True,
    )

    top_masters = top_masters[:3]

    return DashboardData(
        anchor_date=anchor_date,

        revenue_current=revenue_current,
        revenue_previous=revenue_previous,

        bookings_current=len(current_bookings),
        bookings_previous=len(previous_bookings),

        clients_current=clients_current,
        clients_previous=clients_previous,

        masters_current=masters_current,
        masters_previous=masters_previous,

        bookings_today=len(today_bookings),
        completed_today=completed_today,
        cancelled_today=cancelled_today,
        noshow_today=noshow_today,

        recent_bookings=recent_bookings,
        today_schedule=today_schedule,
        top_masters=top_masters,

        # Підключимо, коли матимемо API endpoints
        new_reviews_today=0,
        low_ratings_today=0,
        ai_searches_today=0,
    )