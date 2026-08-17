from datetime import datetime, timedelta

from nicegui import ui
from pages.layout import add_navigation
from database import get_connection


def _pct_change(current: float, previous: float) -> str:
    if previous == 0:
        return "+100%" if current > 0 else "0%"
    change = (current - previous) / previous * 100
    sign = "+" if change >= 0 else ""
    return f"{sign}{change:.1f}%"


def _kpi_card(title: str, value: str, change: str, icon: str, color: str) -> None:
    is_positive = change.startswith("+") or change == "0%"
    change_color = "text-green-600" if is_positive else "text-gray-500"
    triangle = "▲" if is_positive else "▼"
    change_value = change.lstrip("+-")

    with ui.card().classes("p-5 flex-1 min-w-[220px] rounded-2xl shadow-sm"):

        # Заголовок зверху
        ui.label(title).classes("text-xs text-gray-500 mb-0")

        # Іконка + значення + тренд
        with ui.row().classes("items-center justify-between w-full"):

            with ui.row().classes("items-center gap-3"):
                ui.icon(icon).classes(f"text-2xl {color}")
                ui.label(value).classes("text-2xl font-bold")

            ui.label(f"{triangle} {change_value}").classes(
                f"text-sm font-medium {change_color}"
            )

def _stat_card(title: str, value: str, icon: str, color: str) -> None:
    with ui.card().classes("p-5 flex-1 min-w-[220px] rounded-2xl shadow-sm "):

        ui.label(title).classes("text-xs text-gray-500 mb-0")

        with ui.row().classes("items-center gap-3"):
            ui.icon(icon).classes(f"text-2xl {color}")
            ui.label(value).classes("text-2xl font-bold")


@ui.page("/dashboard")
def dashboard_page() -> None:

    add_navigation(active="/dashboard")

    ui.query("body").style("background:#F5F6FA")

    ui.label("Dashboard").classes("text-3xl font-bold m-6 mb-1")
    ui.label("Operational overview — what's happening right now").classes(
        "text-sm text-gray-500 px-6 mb-4"
    )

    conn = get_connection()
    cursor = conn.cursor()

    # =====================================================
    # Anchor "today" to the latest booking in the dataset
    # =====================================================

    anchor_row = cursor.execute(
        "SELECT MAX(booking_datetime) AS latest FROM bookings"
    ).fetchone()
    anchor_dt = datetime.fromisoformat(anchor_row["latest"])
    today_str = anchor_dt.strftime("%Y-%m-%d")

    current_start = anchor_dt - timedelta(days=29)
    previous_start = current_start - timedelta(days=30)
    previous_end = current_start - timedelta(seconds=1)

    def fmt(dt: datetime) -> str:
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    # =====================================================
    # KPI cards (30-day rolling window vs previous 30 days)
    # =====================================================

    cur_revenue = cursor.execute(
        "SELECT COALESCE(SUM(amount),0) AS t FROM payments WHERE payment_date BETWEEN ? AND ?",
        (fmt(current_start), fmt(anchor_dt)),
    ).fetchone()["t"]
    prev_revenue = cursor.execute(
        "SELECT COALESCE(SUM(amount),0) AS t FROM payments WHERE payment_date BETWEEN ? AND ?",
        (fmt(previous_start), fmt(previous_end)),
    ).fetchone()["t"]

    cur_bookings = cursor.execute(
        "SELECT COUNT(*) AS t FROM bookings WHERE booking_datetime BETWEEN ? AND ?",
        (fmt(current_start), fmt(anchor_dt)),
    ).fetchone()["t"]
    prev_bookings = cursor.execute(
        "SELECT COUNT(*) AS t FROM bookings WHERE booking_datetime BETWEEN ? AND ?",
        (fmt(previous_start), fmt(previous_end)),
    ).fetchone()["t"]

    cur_clients = cursor.execute(
        "SELECT COUNT(*) AS t FROM clients WHERE registration_date BETWEEN ? AND ?",
        (current_start.strftime("%Y-%m-%d"), today_str),
    ).fetchone()["t"]
    prev_clients = cursor.execute(
        "SELECT COUNT(*) AS t FROM clients WHERE registration_date BETWEEN ? AND ?",
        (previous_start.strftime("%Y-%m-%d"), previous_end.strftime("%Y-%m-%d")),
    ).fetchone()["t"]

    cur_masters = cursor.execute(
        "SELECT COUNT(DISTINCT master_id) AS t FROM bookings WHERE booking_datetime BETWEEN ? AND ?",
        (fmt(current_start), fmt(anchor_dt)),
    ).fetchone()["t"]
    prev_masters = cursor.execute(
        "SELECT COUNT(DISTINCT master_id) AS t FROM bookings WHERE booking_datetime BETWEEN ? AND ?",
        (fmt(previous_start), fmt(previous_end)),
    ).fetchone()["t"]

    with ui.element("div").classes(
       "grid gap-4 px-6 w-full grid-cols-1 md:grid-cols-2 xl:grid-cols-4"):

        _kpi_card(
            "Total Revenue (30d)",
            f"${cur_revenue/1000:.1f}K",
            _pct_change(cur_revenue, prev_revenue),
            "payments",
            "text-purple-600",
        )
        _kpi_card(
            "Total Bookings (30d)",
            str(cur_bookings),
            _pct_change(cur_bookings, prev_bookings),
            "event",
            "text-purple-600",
        )
        _kpi_card(
            "New Clients (30d)",
            str(cur_clients),
            _pct_change(cur_clients, prev_clients),
            "groups",
            "text-purple-600",
        )
        _kpi_card(
            "Active Masters (30d)",
            str(cur_masters),
            _pct_change(cur_masters, prev_masters),
            "badge",
            "text-purple-600",
        )

    ui.separator().classes("my-5")

    # =====================================================
    # Today's operational stats
    # =====================================================

    ui.label("Today").classes("text-lg font-bold px-6 mb-2")

    bookings_today = cursor.execute(
        "SELECT COUNT(*) AS t FROM bookings WHERE DATE(booking_datetime) = ?",
        (today_str,),
    ).fetchone()["t"]
    completed_today = cursor.execute(
        "SELECT COUNT(*) AS t FROM bookings WHERE DATE(booking_datetime) = ? AND status = 'Completed'",
        (today_str,),
    ).fetchone()["t"]
    cancelled_today = cursor.execute(
        "SELECT COUNT(*) AS t FROM bookings WHERE DATE(booking_datetime) = ? AND status = 'Cancelled'",
        (today_str,),
    ).fetchone()["t"]
    noshow_today = cursor.execute(
        "SELECT COUNT(*) AS t FROM bookings WHERE DATE(booking_datetime) = ? AND status = 'No-show'",
        (today_str,),
    ).fetchone()["t"]

    with ui.element("div").classes(
        "grid gap-4 px-6 w-full grid-cols-1 md:grid-cols-2 xl:grid-cols-4"
    ):
        _stat_card("Bookings Today", str(bookings_today), "calendar_today", "text-purple-600")
        _stat_card("Completed Today", str(completed_today), "check_circle", "text-green-600")
        _stat_card("Cancelled Today", str(cancelled_today), "cancel", "text-gray-600")
        _stat_card("No-show Today", str(noshow_today), "person_off", "text-gray-600")

    ui.separator().classes("my-5")

    
   # =====================================================
    # Recent Bookings + Today's Schedule
    # =====================================================

    with ui.row().classes("px-6 gap-4 w-full flex-wrap items-stretch"):

        with ui.card().classes("p-4 flex-1 min-w-[650px] h-[500px] rounded-2xl shadow-sm").props("flat"):
            ui.label("Recent Bookings").classes("text-lg font-semibold mb-2")

            recent_bookings = cursor.execute("""
                SELECT
                    b.booking_id AS id,
                    c.client_name AS client,
                    m.master_name AS master,
                    b.booking_datetime AS booking_datetime,
                    b.status AS status
                FROM bookings b
                JOIN clients c ON c.client_id = b.client_id
                JOIN masters m ON m.master_id = b.master_id
                ORDER BY b.booking_datetime DESC
                LIMIT 30
            """).fetchall()

            columns = [
                {"name": "id", "label": "ID", "field": "id", "align": "left", "style": "width:60px"},
                {"name": "client", "label": "Client", "field": "client", "align": "left", "style": "width:170px"},
                {"name": "master", "label": "Master", "field": "master", "align": "left", "style": "width:170px"},
                {"name": "datetime", "label": "Date / Time", "field": "datetime", "align": "left", "style": "width:130px"},
                {"name": "status", "label": "Status", "field": "status", "align": "center", "style": "width:100px"},
            ]
            rows = [
                {
                    "id": r["id"],
                    "client": r["client"],
                    "master": r["master"],
                    "datetime": r["booking_datetime"][:16].replace("T", " "),
                    "status": r["status"],
                }
                for r in recent_bookings
            ]

            ui.table(
                columns=columns,
                rows=rows,
                row_key="id",
                pagination=12,
            ).props(
                'dense flat separator=horizontal :rows-per-page-options="[12]"'
            ).classes("w-full").style("table-layout: fixed;")

        with ui.card().classes("p-4 flex-1 min-w-[500px] h-[500px] rounded-2xl shadow-sm").props("flat"):
            ui.label("Today's Schedule").classes("text-lg font-semibold mb-2")

            schedule = cursor.execute(
                """
                SELECT
                    m.master_name AS master,
                    c.client_name AS client,
                    s.service_name AS service,
                    b.booking_datetime AS booking_datetime,
                    b.status AS status
                FROM bookings b
                JOIN clients c ON c.client_id = b.client_id
                JOIN masters m ON m.master_id = b.master_id
                JOIN services s ON s.service_id = b.service_id
                WHERE DATE(b.booking_datetime) = ?
                ORDER BY b.booking_datetime ASC
                """,
                (today_str,),
            ).fetchall()

            with ui.scroll_area().classes("w-full h-[430px]"):
                if not schedule:
                    ui.label("No bookings scheduled for today.").classes("text-sm text-gray-500")

                for item in schedule:
                    time_label = item["booking_datetime"][11:16]
                    with ui.row().classes("items-center justify-between w-full py-1 border-b"):
                        with ui.column().classes("gap-0"):
                            ui.label(f"{time_label} — {item['client']}").classes("font-medium text-sm")
                            ui.label(f"{item['service']} · {item['master']}").classes(
                                "text-xs text-gray-500"
                            )
                        ui.label(item["status"]).classes("text-xs text-gray-500")

    ui.separator().classes("my-5")

   # =====================================================
    # Top Masters Today + Alerts
    # =====================================================

    with ui.row().classes("px-6 gap-4 w-full flex-wrap items-stretch"):

        with ui.card().classes("flex-1 min-w-[500px] p-4 rounded-2xl shadow-sm"):

            ui.label("Top Masters Today").classes("text-lg font-semibold mb-2")

            top_masters = cursor.execute(
                """
                SELECT
                    m.master_name AS name,
                    COUNT(DISTINCT b.booking_id) AS bookings_today,
                    COALESCE(SUM(p.amount), 0) AS revenue_today,
                    m.rating_base AS rating
                FROM bookings b
                JOIN masters m ON m.master_id = b.master_id
                LEFT JOIN payments p ON p.booking_id = b.booking_id
                WHERE DATE(b.booking_datetime) = ?
                GROUP BY m.master_id, m.master_name, m.rating_base
                ORDER BY bookings_today DESC, rating DESC, revenue_today DESC
                LIMIT 3
                """,
                (today_str,),
            ).fetchall()

            if top_masters:

                medals = ["🥇", "🥈", "🥉"]

                with ui.row().classes("w-full gap-3"):

                    for i, master in enumerate(top_masters):

                        with ui.card().classes("flex-1 p-3 rounded-xl shadow-sm"):

                            ui.label(medals[i]).classes("text-2xl")

                            ui.label(master["name"]).classes("font-semibold text-sm")

                            ui.label(f"⭐ {master['rating']:.1f}").classes(
                                "text-xs text-gray-500"
                            )

                            ui.label(f"{master['bookings_today']} bookings").classes(
                                "text-xs text-gray-500"
                            )

                            ui.label(f"${master['revenue_today']:,.0f}").classes(
                                "text-lg font-bold text-purple-600"
                            )

            else:
                ui.label("No bookings today yet.").classes("text-sm text-gray-500")

        with ui.card().classes("flex-1 min-w-[350px] p-4 rounded-2xl shadow-sm"):

            ui.label("Notifications & Alerts").classes("text-lg font-semibold mb-2")

            new_reviews_today = cursor.execute(
                "SELECT COUNT(*) AS t FROM reviews WHERE DATE(review_date) = ?",
                (today_str,),
            ).fetchone()["t"]
            low_ratings_today = cursor.execute(
                "SELECT COUNT(*) AS t FROM reviews WHERE DATE(review_date) = ? AND rating <= 2",
                (today_str,),
            ).fetchone()["t"]
            ai_searches_today = cursor.execute(
                "SELECT COUNT(*) AS t FROM ai_searches WHERE DATE(search_datetime) = ?",
                (today_str,),
            ).fetchone()["t"]

            alerts = [
                (f"{new_reviews_today} new review(s) today", "rate_review", "text-blue-600"),
                (f"{low_ratings_today} low rating(s) (≤2★) today", "warning", "text-red-600"),
                (f"{ai_searches_today} new AI searches today", "auto_awesome", "text-purple-600"),
            ]

            for text, icon, color in alerts:
                with ui.row().classes("items-center gap-3 py-1"):
                    ui.icon(icon).classes(f"text-xl {color}")
                    ui.label(text).classes("text-sm")

    conn.close()