from datetime import datetime, timedelta
import csv
import io
from nicegui import ui
from pages.layout import add_navigation
from database import get_connection


PERIOD_DAYS = {
    "Last 7 days": 7,
    "Last 30 days": 30,
    "Last 90 days": 90,
    "This year": 365,
}

WEEKDAY_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

ACCENT_COLOR = "#9333ea"  # same purple as Revenue Trend line


def _kpi_card(title: str, value: str, icon: str, color: str, min_width: str = "190px") -> None:
    with ui.card().classes(f"p-4 flex-1 min-w-[{min_width}] shadow-sm rounded-2xl"):
        ui.label(title).classes("text-xs text-gray-500 mb-2")

        with ui.row().classes("items-center gap-3 flex-nowrap"):
            ui.icon(icon).classes(f"text-2xl {color} shrink-0")
            ui.label(value).classes("text-2xl font-bold")


def _chart_card_header(title: str, subtitle: str = "") -> None:
    ui.label(title).classes("text-lg font-semibold mb-1")
    ui.label(subtitle).classes("text-xs text-gray-500 mb-2 min-h-[16px]")


def _hbar_option(categories: list, values: list, formatter: str = "{b}: {c}") -> dict:
    """Horizontal bar: no value-axis scale, label at the end of each bar."""
    return {
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}, "formatter": formatter},
        "grid": {"left": "2%", "right": "12%", "top": "2%", "bottom": "2%", "containLabel": True},
        "xAxis": {"type": "value", "show": False},
        "yAxis": {
            "type": "category",
            "data": categories,
            "axisLabel": {"interval": 0},
        },
        "series": [
            {
                "type": "bar",
                "data": values,
                "itemStyle": {"color": ACCENT_COLOR, "borderRadius": [0, 6, 6, 0]},
                "label": {"show": True, "position": "right", "formatter": "${c}K"},
            }
        ],
    }


def _vbar_option(categories: list, values: list, rotate: int = 0, formatter: str = "{b}: {c}") -> dict:
    """Vertical bar chart with zero labels hidden."""
    is_money = "K" in formatter

    formatted_series_data = [
        val if val > 0 else {"value": 0, "label": {"show": False}}
        for val in values
    ]

    return {
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}, "formatter": formatter},
        "grid": {"left": "2%", "right": "2%", "top": "12%", "bottom": "2%", "containLabel": True},
        "xAxis": {
            "type": "category",
            "data": categories,
            "axisLabel": {"interval": 0, "rotate": rotate},
        },
        "yAxis": {"type": "value", "show": False},
        "series": [
            {
                "type": "bar",
                "data": formatted_series_data,
                "itemStyle": {"color": ACCENT_COLOR, "borderRadius": [6, 6, 0, 0]},
                "label": {
                    "show": True,
                    "position": "top",
                    "formatter": "${c}K" if is_money else "{c}",
                },
            }
        ],
    }


@ui.page("/analytics")
def analytics_page() -> None:

    add_navigation(active="/analytics")

    ui.query("body").style("background:#F5F6FA")

    ui.label("Analytics").classes("text-3xl font-bold m-6 mb-1")
    ui.label("Business performance and trends").classes("text-sm text-gray-500 px-6 mb-4")

    conn = get_connection()
    cursor = conn.cursor()

    latest_row = cursor.execute("SELECT MAX(payment_date) AS latest FROM payments").fetchone()
    anchor_date = (
        datetime.fromisoformat(latest_row["latest"])
        if latest_row and latest_row["latest"]
        else datetime.now()
    )

    def get_cutoff(period_label: str) -> str:
        days = PERIOD_DAYS.get(period_label, 30)
        cutoff = anchor_date - timedelta(days=days)
        return cutoff.strftime("%Y-%m-%d %H:%M:%S")

    with ui.row().classes("w-full px-6 gap-4 items-center"):

        period_select = ui.select(
            list(PERIOD_DAYS.keys()),
            value="Last 30 days",
            label="Period",
        ).classes("w-56")

        ui.space()

        def export_report() -> None:
            cutoff = get_cutoff(period_select.value)

            performance = cursor.execute(
                """
                SELECT
                    m.master_name AS name,
                    m.specialization AS category,
                    COUNT(DISTINCT b.booking_id) AS bookings,
                    COALESCE(SUM(p.amount), 0) AS revenue,
                    m.rating_base AS rating
                FROM masters m
                LEFT JOIN bookings b
                    ON b.master_id = m.master_id AND b.booking_datetime >= ?
                LEFT JOIN payments p ON p.booking_id = b.booking_id
                GROUP BY m.master_id
                ORDER BY revenue DESC
                """,
                (cutoff,),
            ).fetchall()

            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(["Master", "Category", "Bookings", "Revenue", "Rating"])
            for r in performance:
                writer.writerow([r["name"], r["category"], r["bookings"], f"{r['revenue']:.2f}", r["rating"]])

            ui.download(buffer.getvalue().encode("utf-8"), f"analytics_report_{period_select.value.replace(' ', '_')}.csv")

        ui.button("Export Report", icon="download", on_click=export_report).classes(
            "bg-purple-600 text-white"
        )

    ui.separator().classes("my-4")

    # =====================================================
    # KPI row
    # =====================================================

    @ui.refreshable
    def kpi_row() -> None:

        cutoff = get_cutoff(period_select.value)

        total_bookings = cursor.execute(
            "SELECT COUNT(*) AS t FROM bookings WHERE booking_datetime >= ?", (cutoff,)
        ).fetchone()["t"]
        cancelled = cursor.execute(
            "SELECT COUNT(*) AS t FROM bookings WHERE booking_datetime >= ? AND status = 'Cancelled'",
            (cutoff,),
        ).fetchone()["t"]
        no_show = cursor.execute(
            "SELECT COUNT(*) AS t FROM bookings WHERE booking_datetime >= ? AND status = 'No-show'",
            (cutoff,),
        ).fetchone()["t"]

        paid_count = cursor.execute(
            "SELECT COUNT(*) AS t FROM payments WHERE payment_date >= ?", (cutoff,)
        ).fetchone()["t"]
        paid_sum = cursor.execute(
            "SELECT COALESCE(SUM(amount),0) AS t FROM payments WHERE payment_date >= ?", (cutoff,)
        ).fetchone()["t"]

        aov = paid_sum / paid_count if paid_count else 0
        cancellation_rate = (cancelled / total_bookings * 100) if total_bookings else 0
        no_show_rate = (no_show / total_bookings * 100) if total_bookings else 0

        repeat_row = cursor.execute(
            """
            SELECT
                COUNT(DISTINCT CASE WHEN prior.client_id IS NOT NULL THEN cur.client_id END) AS returning_count,
                COUNT(DISTINCT cur.client_id) AS total
            FROM bookings cur
            LEFT JOIN bookings prior
                ON prior.client_id = cur.client_id
                AND prior.booking_datetime < ?
            WHERE cur.booking_datetime >= ?
            """,
            (cutoff, cutoff),
        ).fetchone()

        repeat_pct = (
            repeat_row["returning_count"] / repeat_row["total"] * 100 if repeat_row["total"] else 0
        )

        with ui.row().classes("px-6 gap-4 flex-wrap w-full"):
            _kpi_card("Total Revenue", f"${paid_sum/1000:.1f}K", "payments", "text-purple-600")
            _kpi_card("Avg Order Value", f"${aov:,.0f}", "receipt_long", "text-purple-600")
            _kpi_card("Cancellation Rate", f"{cancellation_rate:.1f}%", "cancel", "text-purple-600")
            _kpi_card("No-show Rate", f"{no_show_rate:.1f}%", "person_off", "text-purple-600")
            _kpi_card("Repeat Clients", f"{repeat_pct:.1f}%", "repeat", "text-purple-600")

    kpi_row()

    ui.separator().classes("my-4")

    # =====================================================
    # Revenue Trend + Payment Methods
    # =====================================================

    @ui.refreshable
    def revenue_and_payment_charts() -> None:
        cutoff = get_cutoff(period_select.value)

        with ui.row().classes("px-6 gap-4 w-full flex-wrap items-stretch"):
            with ui.card().classes("p-4 flex-1 min-w-[500px] rounded-2xl"):
                _chart_card_header("Revenue Trend")

                revenue_trend = cursor.execute(
                    """
                    SELECT DATE(payment_date) AS day, SUM(amount) AS total
                    FROM payments
                    WHERE payment_date >= ?
                    GROUP BY DATE(payment_date)
                    ORDER BY day
                    """,
                    (cutoff,),
                ).fetchall()

                # Перетворюємо '2026-07-20' -> '20 Jul 26'
                dates = [
                    datetime.strptime(r["day"], "%Y-%m-%d").strftime("%d %b %y")
                    for r in revenue_trend
                ]
                revenue_in_k = [round(r["total"] / 1000.0, 1) for r in revenue_trend]

                ui.echart(
                    {
                        "tooltip": {
                            "trigger": "axis",
                            "formatter": "{b}<br/>Revenue: ${c}K",
                        },
                        "grid": {
                            "left": "2%",
                            "right": "3%",
                            "top": "10%",
                            "bottom": "2%",
                            "containLabel": True,
                        },
                        "xAxis": {
                            "type": "category",
                            "data": dates,
                            "axisLabel": {
                                "interval": "auto",
                                "rotate": 0,
                            },
                        },
                        "yAxis": {
                            "type": "value",
                            "axisLabel": {"formatter": "${value}K"},
                            "splitNumber": 3,  # Зменшуємо кількість значень на осі
                            "splitLine": {
                                "show": False  # Повністю ПРИБИРАЄМО горизонтальну сітку
                            },
                            "axisLine": {
                                "show": True,  # МАЛЮЄМО вертикальну лінію осі ординат (Y)
                                "lineStyle": {
                                    "color": "#9ca3af"  # Колір лінії осі
                                }
                            },
                            "axisTick": {
                                "show": True   # Додаємо маленькі засічки на лінійці (опціонально)
                            }
                        },
                        "series": [
                            {
                                "type": "line",
                                "smooth": True,
                                "data": revenue_in_k,
                                "symbolSize": 6,
                                "itemStyle": {"color": ACCENT_COLOR},
                                "areaStyle": {"opacity": 0.15, "color": ACCENT_COLOR},
                            }
                        ],
                    }
                ).classes("w-full h-64")

            with ui.card().classes("p-4 flex-1 min-w-[350px] rounded-2xl"):
                _chart_card_header("Payment Methods")

                method_counts = cursor.execute(
                    """
                    SELECT payment_method, COUNT(*) AS total
                    FROM payments
                    WHERE payment_date >= ?
                    GROUP BY payment_method
                    """,
                    (cutoff,),
                ).fetchall()

                ui.echart(
                    {
                        "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
                        "series": [
                            {
                                "type": "pie",
                                "radius": ["40%", "70%"],
                                "label": {"show": True, "formatter": "{b}\n{c} ({d}%)"},
                               "data": [{"name": r["payment_method"], "value": r["total"], "itemStyle": {"color": c}} for r, c in zip(method_counts, ["#9333ea", "#c084fc", "#e9d5ff", "#818cf8"])],
                            }
                        ],
                    }
                ).classes("w-full h-64")

    revenue_and_payment_charts()

    ui.separator().classes("my-4")

    # =====================================================
    # Revenue by Period (Day/Week/Month) + Revenue by City
    # =====================================================

    @ui.refreshable
    def revenue_month_city_charts() -> None:

        cutoff = get_cutoff(period_select.value)

        with ui.row().classes("px-6 gap-4 w-full flex-wrap items-stretch"):

            with ui.card().classes("p-4 flex-1 min-w-[450px] rounded-2xl"):

                if period_select.value == "Last 7 days":
                    title = "Revenue by Day"
                    sql = """
                    SELECT strftime('%d.%m', payment_date) AS period,
                           SUM(amount) AS total
                    FROM payments
                    WHERE payment_date >= ?
                    GROUP BY DATE(payment_date)
                    ORDER BY DATE(payment_date)
                    """
                elif period_select.value == "Last 30 days":
                    title = "Revenue by Week"
                    sql = """
                    SELECT MIN(DATE(payment_date)) AS period,
                        SUM(amount) AS total
                    FROM payments
                    WHERE payment_date >= ?
                    GROUP BY strftime('%Y-%W', payment_date)
                    ORDER BY MIN(payment_date)
                    """
                else:  # Last 90 days + This year
                    title = "Revenue by Month"
                    sql = """
                    SELECT
                        CASE strftime('%m', payment_date)
                            WHEN '01' THEN 'Jan'
                            WHEN '02' THEN 'Feb'
                            WHEN '03' THEN 'Mar'
                            WHEN '04' THEN 'Apr'
                            WHEN '05' THEN 'May'
                            WHEN '06' THEN 'Jun'
                            WHEN '07' THEN 'Jul'
                            WHEN '08' THEN 'Aug'
                            WHEN '09' THEN 'Sep'
                            WHEN '10' THEN 'Oct'
                            WHEN '11' THEN 'Nov'
                            WHEN '12' THEN 'Dec'
                        END AS period,
                        SUM(amount) AS total
                    FROM payments
                    WHERE payment_date >= ?
                    GROUP BY strftime('%Y-%m', payment_date)
                    ORDER BY strftime('%Y-%m', payment_date)
                    """

                by_period = cursor.execute(sql, (cutoff,)).fetchall()

                if period_select.value == "Last 30 days":
                    x_categories = [
                        datetime.strptime(r["period"], "%Y-%m-%d").strftime("%d %b") 
                        for r in by_period
                    ]
                else:
                    x_categories = [r["period"] for r in by_period]

                _chart_card_header(title)

                ui.echart(
                    _vbar_option(
                        x_categories,  # <-- ВИПРАВЛЕНО: тепер використовуємо x_categories
                        [round(r["total"] / 1000, 1) for r in by_period],
                        formatter="{b}<br/>${c}K",
                    )
                ).classes("w-full").style("height: 300px")

            with ui.card().classes("p-4 flex-1 min-w-[450px] rounded-2xl"):
                _chart_card_header("Revenue by City")

                by_city = cursor.execute(
                    """
                    SELECT m.city AS city, COALESCE(SUM(p.amount), 0) AS total
                    FROM bookings b
                    JOIN masters m ON m.master_id = b.master_id
                    LEFT JOIN payments p ON p.booking_id = b.booking_id
                    WHERE b.booking_datetime >= ?
                    GROUP BY m.city
                    ORDER BY total DESC
                    LIMIT 10
                    """,
                    (cutoff,),
                ).fetchall()

                ui.echart(
                    _hbar_option(
                        [r["city"] for r in by_city][::-1],
                        [round(r["total"] / 1000, 1) for r in by_city][::-1],
                        formatter="{b}: ${c}K",
                    )
                ).classes("w-full").style("height: 300px")

    revenue_month_city_charts()

    ui.separator().classes("my-4")

    @ui.refreshable
    def masters_services_charts() -> None:

        cutoff = get_cutoff(period_select.value)

        with ui.row().classes("px-6 gap-4 w-full flex-wrap items-stretch"):

            with ui.card().classes("p-4 flex-1 min-w-[400px] rounded-2xl"):
                _chart_card_header("Top Masters by Bookings")

                top_masters = cursor.execute(
                    """
                    SELECT m.master_name AS name, COUNT(b.booking_id) AS bookings
                    FROM masters m
                    LEFT JOIN bookings b
                        ON b.master_id = m.master_id AND b.booking_datetime >= ?
                    GROUP BY m.master_id
                    ORDER BY bookings DESC
                    LIMIT 10
                    """,
                    (cutoff,),
                ).fetchall()

                ui.echart(
                    _hbar_option(
                        [m["name"] for m in top_masters][::-1],
                        [m["bookings"] for m in top_masters][::-1],
                    )
                ).classes("w-full").style("height: 320px")

            with ui.card().classes("p-4 flex-1 min-w-[400px] rounded-2xl"):
                _chart_card_header("Most Popular Services")

                popular_services = cursor.execute(
                    """
                    SELECT s.service_name AS name, COUNT(b.booking_id) AS bookings
                    FROM bookings b
                    JOIN services s ON s.service_id = b.service_id
                    WHERE b.booking_datetime >= ?
                    GROUP BY s.service_id
                    ORDER BY bookings DESC
                    LIMIT 10
                    """,
                    (cutoff,),
                ).fetchall()

                # --- ЗМІНИ ТУТ: перетворили на _hbar_option з розвертанням списків [::-1] ---
                ui.echart(
                    _hbar_option(
                        [s["name"] for s in popular_services][::-1],
                        [s["bookings"] for s in popular_services][::-1],
                    )
                ).classes("w-full").style("height: 320px")

    masters_services_charts()

    ui.separator().classes("my-4")

    # =====================================================
    # Booking Status + New vs Returning Clients
    # =====================================================

    @ui.refreshable
    def status_clients_charts() -> None:

        cutoff = get_cutoff(period_select.value)

        with ui.row().classes("px-6 gap-4 w-full flex-wrap items-stretch"):

            with ui.card().classes("p-4 flex-1 min-w-[350px] rounded-2xl"):
                _chart_card_header("Booking Status")

                status_counts = cursor.execute(
                    """
                    SELECT status, COUNT(*) AS total
                    FROM bookings
                    WHERE booking_datetime >= ?
                    GROUP BY status
                    """,
                    (cutoff,),
                ).fetchall()
                ui.echart(
                    {
                        "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
                        "series": [
                            {
                                "type": "pie",
                                "radius": ["40%", "70%"],
                                "label": {"show": True, "formatter": "{b}\n{c} ({d}%)"},
                                "data": [
                                    {"name": r["status"], "value": r["total"]}
                                    for r in status_counts
                                ],
                                "color": [
                                    "#64748b",  # Cancelled
                                    "#9333ea",  # Confirmed
                                    "#CBD5E1",  # No-show
                                ],
                            }
                        ],
                    }
                ).classes("w-full h-64")

            with ui.card().classes("p-4 flex-1 min-w-[350px] rounded-2xl"):
                _chart_card_header("New vs Returning Clients")

                repeat_row = cursor.execute(
                    """
                    SELECT
                        COUNT(DISTINCT CASE WHEN prior.client_id IS NOT NULL THEN cur.client_id END) AS returning_count,
                        COUNT(DISTINCT cur.client_id) AS total
                    FROM bookings cur
                    LEFT JOIN bookings prior
                        ON prior.client_id = cur.client_id
                        AND prior.booking_datetime < ?
                    WHERE cur.booking_datetime >= ?
                    """,
                    (cutoff, cutoff),
                ).fetchone()

                returning = repeat_row["returning_count"] or 0
                new_clients = (repeat_row["total"] or 0) - returning

                ui.echart(
                    {
                        "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
                        "series": [
                            {
                                "type": "pie",
                                "radius": ["40%", "70%"],
                                "label": {"show": True, "formatter": "{b}\n{c} ({d}%)"},
                                "data": [
                                    {"name": "New", "value": new_clients},
                                    {"name": "Returning", "value": returning},
                                ],
                                "color": ["#c4b5fd", ACCENT_COLOR],
                            }
                        ],
                    }
                ).classes("w-full h-64")

    status_clients_charts()

    ui.separator().classes("my-4")

    # =====================================================
    # Peak Hours + Bookings by Weekday
    # =====================================================

    @ui.refreshable
    def hours_weekday_charts() -> None:
        cutoff = get_cutoff(period_select.value)

        # ДОДАНО: з'єднання з базою даних
        with get_connection() as conn:
            cursor = conn.cursor()

            by_hour = cursor.execute(
                """
                SELECT CAST(strftime('%H', booking_datetime) AS INTEGER) AS hour, COUNT(*) AS total
                FROM bookings
                WHERE booking_datetime >= ? AND booking_datetime IS NOT NULL
                GROUP BY hour
                ORDER BY hour
                """,
                (cutoff,),
            ).fetchall()

            by_weekday = cursor.execute(
                """
                SELECT strftime('%w', booking_datetime) AS wd, COUNT(*) AS total
                FROM bookings
                WHERE booking_datetime >= ? AND booking_datetime IS NOT NULL
                GROUP BY wd
                """,
                (cutoff,),
            ).fetchall()

        # 1. Обробка Peak Hours (тільки активні години)
        active_hours = [r for r in by_hour if r["hour"] is not None and r["total"] > 0]
        categories_hours = [f"{int(r['hour']):02d}:00" for r in active_hours]
        values_hours = [r["total"] for r in active_hours]

        # 2. Обробка Bookings by Weekday (з понеділка по неділю)
        weekday_map = {int(r["wd"]): r["total"] for r in by_weekday if r["wd"] is not None}
        
        # Порядок: Mon (1), Tue (2), Wed (3), Thu (4), Fri (5), Sat (6), Sun (0)
        eu_weekday_order = [1, 2, 3, 4, 5, 6, 0]
        eu_weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        values_weekdays = [weekday_map.get(w, 0) for w in eu_weekday_order]

        with ui.row().classes("px-6 gap-4 w-full flex-wrap items-stretch"):
            with ui.card().classes("p-4 flex-1 min-w-[450px] rounded-2xl"):
                _chart_card_header("Peak Hours")
                ui.echart(
                    _vbar_option(
                        categories_hours,
                        values_hours,
                        formatter="{b}<br/>Bookings: {c}",
                    )
                ).classes("w-full h-64")

            with ui.card().classes("p-4 flex-1 min-w-[400px] rounded-2xl"):
                _chart_card_header("Bookings by Weekday")
                ui.echart(
                    _vbar_option(
                        eu_weekday_names,
                        values_weekdays,
                        formatter="{b}<br/>Bookings: {c}",
                    )
                ).classes("w-full h-64")

    hours_weekday_charts()
    ui.separator().classes("my-4")

    # =====================================================
    # AI Analyses stat cards
    # =====================================================

    @ui.refreshable
    def ai_stats() -> None:

        cutoff = get_cutoff(period_select.value)

        ai_total = cursor.execute(
            "SELECT COUNT(*) AS t FROM ai_searches WHERE search_datetime >= ?", (cutoff,)
        ).fetchone()["t"]
        ai_accepted = cursor.execute(
            "SELECT COUNT(*) AS t FROM ai_searches WHERE search_datetime >= ? AND recommendation_accepted = 1",
            (cutoff,),
        ).fetchone()["t"]
        conversion = (ai_accepted / ai_total * 100) if ai_total else 0

        ui.label("AI Performance").classes("text-lg font-bold px-6 mb-2")

        with ui.row().classes("px-6 gap-4 flex-wrap"):
            _kpi_card("AI Analyses", str(ai_total), "auto_awesome", "text-purple-600", min_width="260px")
            _kpi_card(
                "AI → Booking Conversion",
                f"{conversion:.1f}%",
                "trending_up",
                "text-purple-600",
                min_width="280px",
            )

    ai_stats()

    ui.separator().classes("my-4")

    # =====================================================
    # Master Performance table
    # =====================================================

    with ui.row().classes("px-6 gap-4 items-center mb-2"):
        master_search_input = ui.input(
            placeholder="Search master..."
        ).props("outlined dense").classes("w-80")

        master_category_filter = ui.select(
            ["All", "Hair", "Barber", "Makeup", "Nails", "Brows", "Lashes",
             "Cosmetology", "Laser", "SPA", "Skincare"],
            value="All",
            label="Specialization",
        ).classes("w-56")

    @ui.refreshable
    def master_performance_table() -> None:

        cutoff = get_cutoff(period_select.value)

        ui.label("Master Performance").classes("text-xl font-bold px-6 mb-2")

        query = """
            SELECT
                m.master_name AS name,
                m.specialization AS category,
                COUNT(DISTINCT b.booking_id) AS bookings,
                COALESCE(SUM(p.amount), 0) AS revenue,
                m.rating_base AS rating
            FROM masters m
            LEFT JOIN bookings b
                ON b.master_id = m.master_id AND b.booking_datetime >= ?
            LEFT JOIN payments p ON p.booking_id = b.booking_id
            WHERE 1=1
        """
        params = [cutoff]

        if master_search_input.value:
            query += " AND m.master_name LIKE ?"
            params.append(f"%{master_search_input.value}%")

        if master_category_filter.value and master_category_filter.value != "All":
            query += " AND m.specialization = ?"
            params.append(master_category_filter.value)

        query += " GROUP BY m.master_id ORDER BY revenue DESC"

        performance = cursor.execute(query, params).fetchall()
            

        columns = [
            {"name": "name", "label": "Master", "field": "name", "align": "left"},
            {"name": "category", "label": "Category", "field": "category"},
            {"name": "bookings", "label": "Bookings", "field": "bookings"},
            {"name": "revenue", "label": "Revenue", "field": "revenue"},
            {"name": "rating", "label": "Rating", "field": "rating"},
        ]

        rows = [
            {
                "name": r["name"],
                "category": r["category"],
                "bookings": r["bookings"],
                "revenue": f"${r['revenue']:,.0f}",
                "rating": r["rating"],
            }
            for r in performance
        ]

        with ui.card().classes("mx-6 mb-6 w-full rounded-2xl p-4"):

            ui.table(
                columns=columns,
                rows=rows,
                row_key="name",
                pagination={
                    "rowsPerPage": 10,
                    "sortBy": "bookings",
                    "descending": True,
                },
            ).props(
                "flat bordered separator=horizontal"
            ).classes("w-full")

    master_performance_table()

    def on_period_change() -> None:
        kpi_row.refresh()
        revenue_and_payment_charts.refresh()
        revenue_month_city_charts.refresh()
        masters_services_charts.refresh()
        status_clients_charts.refresh()
        hours_weekday_charts.refresh()
        ai_stats.refresh()
        master_performance_table.refresh()

    period_select.on_value_change(on_period_change)
    master_search_input.on("keydown.enter", master_performance_table.refresh)
    master_category_filter.on_value_change(master_performance_table.refresh)

    period_select.on_value_change(on_period_change)