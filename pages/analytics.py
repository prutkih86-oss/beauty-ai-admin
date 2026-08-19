from datetime import datetime, timedelta
from collections import Counter, defaultdict
import csv
import io

from nicegui import ui

from pages.layout import add_navigation
from data_access.bookings import get_bookings
from data_access.clients import get_clients
from data_access.masters import get_masters
from data_access.services import get_services

try:
    from data_access.payments import get_payments
except (ImportError, AttributeError):
    get_payments = None


PERIOD_DAYS = {
    "Last 7 days": 7,
    "Last 30 days": 30,
    "Last 90 days": 90,
    "This year": 365,
}

WEEKDAY_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

ACCENT_COLOR = "#9333ea"


# =========================================================
# Helpers
# =========================================================

def _kpi_card(
    title: str,
    value: str,
    icon: str,
    color: str,
    min_width: str = "190px",
) -> None:

    with ui.card().classes(
        f"p-4 flex-1 min-w-[{min_width}] shadow-sm rounded-2xl"
    ):
        ui.label(title).classes("text-xs text-gray-500 mb-2")

        with ui.row().classes("items-center gap-3 flex-nowrap"):
            ui.icon(icon).classes(f"text-2xl {color} shrink-0")
            ui.label(value).classes("text-2xl font-bold")


def _chart_card_header(title: str, subtitle: str = "") -> None:

    ui.label(title).classes("text-lg font-semibold mb-1")
    ui.label(subtitle).classes(
        "text-xs text-gray-500 mb-2 min-h-[16px]"
    )


def _hbar_option(
    categories: list,
    values: list,
    formatter: str = "{b}: {c}",
) -> dict:

    return {
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"},
            "formatter": formatter,
        },
        "grid": {
            "left": "2%",
            "right": "12%",
            "top": "2%",
            "bottom": "2%",
            "containLabel": True,
        },
        "xAxis": {
            "type": "value",
            "show": False,
        },
        "yAxis": {
            "type": "category",
            "data": categories,
            "axisLabel": {"interval": 0},
        },
        "series": [
            {
                "type": "bar",
                "data": values,
                "itemStyle": {
                    "color": ACCENT_COLOR,
                    "borderRadius": [0, 6, 6, 0],
                },
                "label": {
                    "show": True,
                    "position": "right",
                    "formatter": "${c}K"
                    if "K" in formatter
                    else "{c}",
                },
            }
        ],
    }


def _vbar_option(
    categories: list,
    values: list,
    rotate: int = 0,
    formatter: str = "{b}: {c}",
) -> dict:

    is_money = "K" in formatter

    formatted_series_data = [
        val
        if val > 0
        else {
            "value": 0,
            "label": {"show": False},
        }
        for val in values
    ]

    return {
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"},
            "formatter": formatter,
        },
        "grid": {
            "left": "2%",
            "right": "2%",
            "top": "12%",
            "bottom": "2%",
            "containLabel": True,
        },
        "xAxis": {
            "type": "category",
            "data": categories,
            "axisLabel": {
                "interval": 0,
                "rotate": rotate,
            },
        },
        "yAxis": {
            "type": "value",
            "show": False,
        },
        "series": [
            {
                "type": "bar",
                "data": formatted_series_data,
                "itemStyle": {
                    "color": ACCENT_COLOR,
                    "borderRadius": [6, 6, 0, 0],
                },
                "label": {
                    "show": True,
                    "position": "top",
                    "formatter": "${c}K"
                    if is_money
                    else "{c}",
                },
            }
        ],
    }


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


def _value(obj, *names, default=None):

    for name in names:

        if isinstance(obj, dict):
            value = obj.get(name)
        else:
            value = getattr(obj, name, None)

        if value is not None:
            return value

    return default


def _load_payments() -> list:

    if get_payments is None:
        return []

    try:
        data = get_payments()

        if data is None:
            return []

        return list(data)

    except Exception as e:
        print(f"[Analytics Payments Error]: {e}")
        return []


# =========================================================
# Page
# =========================================================

@ui.page("/analytics")
def analytics_page() -> None:

    add_navigation(active="/analytics")

    ui.query("body").style("background:#F5F6FA")

    ui.label("Analytics").classes(
        "text-3xl font-bold m-6 mb-1"
    )

    ui.label(
        "Business performance and trends"
    ).classes(
        "text-sm text-gray-500 px-6 mb-4"
    )

    # =====================================================
    # Load API data
    # =====================================================

    try:
        bookings = get_bookings("", "All")
    except Exception as e:
        print(f"[Analytics Bookings Error]: {e}")
        bookings = []

    try:
        clients = get_clients("", "All")
    except Exception as e:
        print(f"[Analytics Clients Error]: {e}")
        clients = []

    try:
        masters = get_masters("", "All")
    except Exception as e:
        print(f"[Analytics Masters Error]: {e}")
        masters = []

    try:
        services = get_services("", "All")
    except Exception as e:
        print(f"[Analytics Services Error]: {e}")
        services = []

    payments = _load_payments()

    parsed_bookings = []

    for booking in bookings:

        dt = _safe_datetime(booking.date_time)

        if dt:
            parsed_bookings.append(
                (booking, dt)
            )

    parsed_payments = []

    for payment in payments:

        payment_date_raw = _value(
            payment,
            "payment_date",
            "date_time",
            "datetime",
            "date",
            "created_at",
        )

        dt = _safe_datetime(payment_date_raw)

        if not dt:
            continue

        amount = _safe_float(
            _value(
                payment,
                "amount",
                "total",
                "price",
                default=0,
            )
        )

        method = str(
            _value(
                payment,
                "payment_method",
                "method",
                "type",
                default="Unknown",
            )
            or "Unknown"
        )

        parsed_payments.append(
            {
                "raw": payment,
                "datetime": dt,
                "amount": amount,
                "method": method,
            }
        )

    # Anchor date

    available_dates = [
        dt for _, dt in parsed_bookings
    ] + [
        p["datetime"]
        for p in parsed_payments
    ]

    if available_dates:
        anchor_date = max(available_dates)
    else:
        anchor_date = datetime.now()

    def get_cutoff(period_label: str) -> datetime:

        days = PERIOD_DAYS.get(
            period_label,
            30,
        )

        return anchor_date - timedelta(
            days=days
        )

    def period_bookings():

        cutoff = get_cutoff(
            period_select.value
        )

        return [
            (booking, dt)
            for booking, dt
            in parsed_bookings
            if dt >= cutoff
        ]

    def period_payments():

        cutoff = get_cutoff(
            period_select.value
        )

        return [
            payment
            for payment
            in parsed_payments
            if payment["datetime"] >= cutoff
        ]

    # Якщо payments API поки не віддає дані,
    # revenue-графіки тимчасово використовують appointment price.
    def revenue_records():

        payment_rows = period_payments()

        if payment_rows:
            return [
                (
                    payment["datetime"],
                    payment["amount"],
                )
                for payment
                in payment_rows
            ]

        return [
            (dt, booking.price)
            for booking, dt
            in period_bookings()
        ]

    # =====================================================
    # Toolbar
    # =====================================================

    with ui.row().classes(
        "w-full px-6 gap-4 items-center"
    ):

        period_select = ui.select(
            list(PERIOD_DAYS.keys()),
            value="Last 30 days",
            label="Period",
        ).classes("w-56")

        ui.space()

        def export_report() -> None:

            filtered = period_bookings()

            stats = defaultdict(
                lambda: {
                    "bookings": 0,
                    "revenue": 0.0,
                }
            )

            for booking, _ in filtered:

                stats[
                    booking.master_name
                ]["bookings"] += 1

                stats[
                    booking.master_name
                ]["revenue"] += booking.price

            master_lookup = {
                master.name: master
                for master in masters
            }

            buffer = io.StringIO()
            writer = csv.writer(buffer)

            writer.writerow(
                [
                    "Master",
                    "Category",
                    "Bookings",
                    "Revenue",
                    "Rating",
                ]
            )

            for name, stat in sorted(
                stats.items(),
                key=lambda x:
                    x[1]["revenue"],
                reverse=True,
            ):

                master = master_lookup.get(
                    name
                )

                writer.writerow(
                    [
                        name,
                        master.specialization
                        if master
                        else "",
                        stat["bookings"],
                        f"{stat['revenue']:.2f}",
                        master.rating
                        if master
                        else 0,
                    ]
                )

            filename = (
                "analytics_report_"
                + period_select.value
                .replace(" ", "_")
                + ".csv"
            )

            ui.download(
                buffer.getvalue().encode(
                    "utf-8"
                ),
                filename,
            )

        ui.button(
            "Export Report",
            icon="download",
            on_click=export_report,
        ).classes(
            "bg-purple-600 text-white"
        )

    ui.separator().classes("my-4")

    # =====================================================
    # KPI row
    # =====================================================

    @ui.refreshable
    def kpi_row() -> None:

        filtered = period_bookings()
        revenue = revenue_records()

        total_bookings = len(filtered)

        cancelled = sum(
            1
            for booking, _
            in filtered
            if booking.status.lower()
            == "cancelled"
        )

        no_show = sum(
            1
            for booking, _
            in filtered
            if booking.status.lower()
            in {
                "no-show",
                "no show",
                "noshow",
            }
        )

        total_revenue = sum(
            amount
            for _, amount
            in revenue
        )

        order_count = (
            len(period_payments())
            if period_payments()
            else total_bookings
        )

        aov = (
            total_revenue / order_count
            if order_count
            else 0
        )

        cancellation_rate = (
            cancelled
            / total_bookings
            * 100
            if total_bookings
            else 0
        )

        no_show_rate = (
            no_show
            / total_bookings
            * 100
            if total_bookings
            else 0
        )

        client_counts = Counter(
            booking.client_name
            for booking, _
            in filtered
            if booking.client_name != "—"
        )

        returning = sum(
            1
            for total
            in client_counts.values()
            if total > 1
        )

        repeat_pct = (
            returning
            / len(client_counts)
            * 100
            if client_counts
            else 0
        )

        with ui.row().classes(
            "px-6 gap-4 flex-wrap w-full"
        ):

            _kpi_card(
                "Booking Value",
                f"${total_revenue / 1000:.1f}K",
                "payments",
                "text-purple-600",
            )

            _kpi_card(
                "Avg Booking Value",
                f"${aov:,.0f}",
                "receipt_long",
                "text-purple-600",
            )

            _kpi_card(
                "Cancellation Rate",
                f"{cancellation_rate:.1f}%",
                "cancel",
                "text-purple-600",
            )

            _kpi_card(
                "No-show Rate",
                f"{no_show_rate:.1f}%",
                "person_off",
                "text-purple-600",
            )

            _kpi_card(
                "Repeat Clients",
                f"{repeat_pct:.1f}%",
                "repeat",
                "text-purple-600",
            )

    kpi_row()

    ui.separator().classes("my-4")

    # =====================================================
    # Revenue Trend + Payment Methods
    # =====================================================

    @ui.refreshable
    def revenue_and_payment_charts() -> None:

        revenue = revenue_records()

        by_day = defaultdict(float)

        for dt, amount in revenue:
            by_day[
                dt.strftime("%Y-%m-%d")
            ] += amount

        sorted_days = sorted(
            by_day.keys()
        )

        dates = [
            datetime.strptime(
                day,
                "%Y-%m-%d",
            ).strftime("%d %b %y")
            for day in sorted_days
        ]

        revenue_in_k = [
            round(
                by_day[day] / 1000,
                1,
            )
            for day in sorted_days
        ]

        method_counts = Counter(
            payment["method"]
            for payment
            in period_payments()
        )

        with ui.row().classes(
            "px-6 gap-4 w-full "
            "flex-wrap items-stretch"
        ):

            # -------------------------
            # Revenue Trend
            # -------------------------

            with ui.card().classes(
                "p-4 flex-1 min-w-[500px] rounded-2xl"
            ):

                _chart_card_header(
                    "Revenue Trend"
                )

                ui.echart(
                    {
                        "tooltip": {
                            "trigger": "axis",
                            "formatter":
                                "{b}<br/>Revenue: ${c}K",
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
                            "axisLabel": {
                                "formatter":
                                    "${value}K"
                            },
                            "splitNumber": 3,
                            "splitLine": {
                                "show": False
                            },
                            "axisLine": {
                                "show": True,
                                "lineStyle": {
                                    "color":
                                        "#9ca3af"
                                },
                            },
                            "axisTick": {
                                "show": True
                            },
                        },
                        "series": [
                            {
                                "type": "line",
                                "smooth": True,
                                "data":
                                    revenue_in_k,
                                "symbolSize": 6,
                                "itemStyle": {
                                    "color":
                                        ACCENT_COLOR
                                },
                                "areaStyle": {
                                    "opacity": 0.15,
                                    "color":
                                        ACCENT_COLOR,
                                },
                            }
                        ],
                    }
                ).classes(
                    "w-full h-64"
                )

            # -------------------------
            # PAYMENT METHODS DONUT
            # -------------------------

            with ui.card().classes(
                "p-4 flex-1 min-w-[350px] rounded-2xl"
            ):

                _chart_card_header(
                    "Payment Methods"
                )

                colors = [
                    "#9333ea",
                    "#c084fc",
                    "#e9d5ff",
                    "#818cf8",
                ]

                donut_data = [
                    {
                        "name": method,
                        "value": count,
                        "itemStyle": {
                            "color":
                                colors[
                                    i % len(colors)
                                ]
                        },
                    }
                    for i, (
                        method,
                        count,
                    ) in enumerate(
                        method_counts.items()
                    )
                ]

                ui.echart(
                    {
                        "tooltip": {
                            "trigger": "item",
                            "formatter":
                                "{b}: {c} ({d}%)",
                        },
                        "series": [
                            {
                                "type": "pie",
                                "radius": [
                                    "40%",
                                    "70%",
                                ],
                                "label": {
                                    "show": True,
                                    "formatter":
                                        "{b}\n{c} ({d}%)",
                                },
                                "data":
                                    donut_data,
                            }
                        ],
                    }
                ).classes(
                    "w-full h-64"
                )

    revenue_and_payment_charts()

    ui.separator().classes("my-4")

    # =====================================================
    # Revenue by Period + Revenue by City
    # =====================================================

    @ui.refreshable
    def revenue_month_city_charts() -> None:

        revenue = revenue_records()

        grouped = defaultdict(float)

        for dt, amount in revenue:

            if (
                period_select.value
                == "Last 7 days"
            ):
                key = dt.strftime(
                    "%d.%m"
                )

            elif (
                period_select.value
                == "Last 30 days"
            ):

                monday = (
                    dt
                    - timedelta(
                        days=dt.weekday()
                    )
                )

                key = monday.strftime(
                    "%d %b"
                )

            else:
                key = dt.strftime(
                    "%b"
                )

            grouped[key] += amount

        x_categories = list(
            grouped.keys()
        )

        period_values = [
            round(
                value / 1000,
                1,
            )
            for value
            in grouped.values()
        ]

        if (
            period_select.value
            == "Last 7 days"
        ):
            title = "Revenue by Day"

        elif (
            period_select.value
            == "Last 30 days"
        ):
            title = "Revenue by Week"

        else:
            title = "Revenue by Month"

        master_city = {
            master.name: master.city
            for master in masters
        }

        city_revenue = defaultdict(
            float
        )

        for booking, _ in period_bookings():

            city = master_city.get(
                booking.master_name,
                "N/A",
            )

            city_revenue[
                city or "N/A"
            ] += booking.price

        top_cities = sorted(
            city_revenue.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:10]

        with ui.row().classes(
            "px-6 gap-4 w-full "
            "flex-wrap items-stretch"
        ):

            with ui.card().classes(
                "p-4 flex-1 "
                "min-w-[450px] rounded-2xl"
            ):

                _chart_card_header(
                    title
                )

                ui.echart(
                    _vbar_option(
                        x_categories,
                        period_values,
                        formatter=
                            "{b}<br/>${c}K",
                    )
                ).classes(
                    "w-full"
                ).style(
                    "height:300px"
                )

            with ui.card().classes(
                "p-4 flex-1 "
                "min-w-[450px] rounded-2xl"
            ):

                _chart_card_header(
                    "Revenue by City"
                )

                ui.echart(
                    _hbar_option(
                        [
                            city
                            for city, _
                            in top_cities
                        ][::-1],
                        [
                            round(
                                amount / 1000,
                                1,
                            )
                            for _, amount
                            in top_cities
                        ][::-1],
                        formatter=
                            "{b}: ${c}K",
                    )
                ).classes(
                    "w-full"
                ).style(
                    "height:300px"
                )

    revenue_month_city_charts()

    ui.separator().classes("my-4")

    # =====================================================
    # Top Masters + Popular Services
    # =====================================================

    @ui.refreshable
    def masters_services_charts() -> None:

        filtered = period_bookings()

        master_counts = Counter(
            booking.master_name
            for booking, _
            in filtered
            if booking.master_name
            and booking.master_name != "—"
        )

        service_counts = Counter(
            booking.service_name
            for booking, _
            in filtered
            if booking.service_name
            and booking.service_name != "—"
        )

        top_masters = (
            master_counts
            .most_common(10)
        )

        popular_services = (
            service_counts
            .most_common(10)
        )

        with ui.row().classes(
            "px-6 gap-4 w-full "
            "flex-wrap items-stretch"
        ):

            with ui.card().classes(
                "p-4 flex-1 "
                "min-w-[400px] rounded-2xl"
            ):

                _chart_card_header(
                    "Top Masters by Bookings"
                )

                ui.echart(
                    _hbar_option(
                        [
                            name
                            for name, _
                            in top_masters
                        ][::-1],
                        [
                            count
                            for _, count
                            in top_masters
                        ][::-1],
                    )
                ).classes(
                    "w-full"
                ).style(
                    "height:320px"
                )

            with ui.card().classes(
                "p-4 flex-1 "
                "min-w-[400px] rounded-2xl"
            ):

                _chart_card_header(
                    "Most Popular Services"
                )

                ui.echart(
                    _hbar_option(
                        [
                            name
                            for name, _
                            in popular_services
                        ][::-1],
                        [
                            count
                            for _, count
                            in popular_services
                        ][::-1],
                    )
                ).classes(
                    "w-full"
                ).style(
                    "height:320px"
                )

    masters_services_charts()

    ui.separator().classes("my-4")

    # =====================================================
    # Booking Status + New vs Returning Clients
    # =====================================================

    @ui.refreshable
    def status_clients_charts() -> None:

        filtered = period_bookings()

        status_counts = Counter(
            booking.status
            for booking, _
            in filtered
        )

        client_counts = Counter(
            booking.client_name
            for booking, _
            in filtered
            if booking.client_name
            and booking.client_name != "—"
        )

        returning = sum(
            1
            for count
            in client_counts.values()
            if count > 1
        )

        new_clients = sum(
            1
            for count
            in client_counts.values()
            if count == 1
        )

        with ui.row().classes(
            "px-6 gap-4 w-full "
            "flex-wrap items-stretch"
        ):

            with ui.card().classes(
                "p-4 flex-1 "
                "min-w-[350px] rounded-2xl"
            ):

                _chart_card_header(
                    "Booking Status"
                )

                ui.echart(
                    {
                        "tooltip": {
                            "trigger": "item",
                            "formatter":
                                "{b}: {c} ({d}%)",
                        },
                        "series": [
                            {
                                "type": "pie",
                                "radius": [
                                    "40%",
                                    "70%",
                                ],
                                "label": {
                                    "show": True,
                                    "formatter":
                                        "{b}\n{c} ({d}%)",
                                },
                                "data": [
                                    {
                                        "name": status,
                                        "value": total,
                                    }
                                    for status, total
                                    in status_counts.items()
                                ],
                                "color": [
                                    "#64748b",
                                    "#9333ea",
                                    "#CBD5E1",
                                ],
                            }
                        ],
                    }
                ).classes(
                    "w-full h-64"
                )

            with ui.card().classes(
                "p-4 flex-1 "
                "min-w-[350px] rounded-2xl"
            ):

                _chart_card_header(
                    "New vs Returning Clients"
                )

                ui.echart(
                    {
                        "tooltip": {
                            "trigger": "item",
                            "formatter":
                                "{b}: {c} ({d}%)",
                        },
                        "series": [
                            {
                                "type": "pie",
                                "radius": [
                                    "40%",
                                    "70%",
                                ],
                                "label": {
                                    "show": True,
                                    "formatter":
                                        "{b}\n{c} ({d}%)",
                                },
                                "data": [
                                    {
                                        "name": "New",
                                        "value":
                                            new_clients,
                                    },
                                    {
                                        "name":
                                            "Returning",
                                        "value":
                                            returning,
                                    },
                                ],
                                "color": [
                                    "#c4b5fd",
                                    ACCENT_COLOR,
                                ],
                            }
                        ],
                    }
                ).classes(
                    "w-full h-64"
                )

    status_clients_charts()

    ui.separator().classes("my-4")

    # =====================================================
    # Peak Hours + Bookings by Weekday
    # =====================================================

    @ui.refreshable
    def hours_weekday_charts() -> None:

        filtered = period_bookings()

        by_hour = Counter()
        by_weekday = Counter()

        for _, dt in filtered:
            by_hour[dt.hour] += 1
            by_weekday[dt.weekday()] += 1

        active_hours = sorted(
            by_hour.items()
        )

        categories_hours = [
            f"{hour:02d}:00"
            for hour, _
            in active_hours
        ]

        values_hours = [
            count
            for _, count
            in active_hours
        ]

        eu_weekday_names = [
            "Mon",
            "Tue",
            "Wed",
            "Thu",
            "Fri",
            "Sat",
            "Sun",
        ]

        values_weekdays = [
            by_weekday.get(
                weekday,
                0,
            )
            for weekday
            in range(7)
        ]

        with ui.row().classes(
            "px-6 gap-4 w-full "
            "flex-wrap items-stretch"
        ):

            with ui.card().classes(
                "p-4 flex-1 "
                "min-w-[450px] rounded-2xl"
            ):

                _chart_card_header(
                    "Peak Hours"
                )

                ui.echart(
                    _vbar_option(
                        categories_hours,
                        values_hours,
                        formatter=
                            "{b}<br/>Bookings: {c}",
                    )
                ).classes(
                    "w-full h-64"
                )

            with ui.card().classes(
                "p-4 flex-1 "
                "min-w-[400px] rounded-2xl"
            ):

                _chart_card_header(
                    "Bookings by Weekday"
                )

                ui.echart(
                    _vbar_option(
                        eu_weekday_names,
                        values_weekdays,
                        formatter=
                            "{b}<br/>Bookings: {c}",
                    )
                ).classes(
                    "w-full h-64"
                )

    hours_weekday_charts()

    ui.separator().classes("my-4")

    # =====================================================
    # AI Performance
    # =====================================================

    @ui.refreshable
    def ai_stats() -> None:

        # Поки API AI search analytics
        # не підключений.
        ai_total = 0
        ai_accepted = 0

        conversion = (
            ai_accepted
            / ai_total
            * 100
            if ai_total
            else 0
        )

        ui.label(
            "AI Performance"
        ).classes(
            "text-lg font-bold px-6 mb-2"
        )

        with ui.row().classes(
            "px-6 gap-4 flex-wrap"
        ):

            _kpi_card(
                "AI Analyses",
                str(ai_total),
                "auto_awesome",
                "text-purple-600",
                min_width="260px",
            )

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
    # Master Performance
    # =====================================================

    with ui.row().classes(
        "px-6 gap-4 items-center mb-2"
    ):

        master_search_input = ui.input(
            placeholder="Search master..."
        ).props(
            "outlined dense"
        ).classes(
            "w-80"
        )

        master_category_filter = ui.select(
            [
                "All",
                "Hair",
                "Barber",
                "Makeup",
                "Nails",
                "Brows",
                "Lashes",
                "Cosmetology",
                "Laser",
                "SPA",
                "Skincare",
            ],
            value="All",
            label="Specialization",
        ).classes(
            "w-56"
        )

    @ui.refreshable
    def master_performance_table() -> None:

        filtered = period_bookings()

        stats = defaultdict(
            lambda: {
                "bookings": 0,
                "revenue": 0.0,
            }
        )

        for booking, _ in filtered:

            stats[
                booking.master_name
            ]["bookings"] += 1

            stats[
                booking.master_name
            ]["revenue"] += booking.price

        rows = []

        for master in masters:

            if (
                master_search_input.value
                and master_search_input.value.lower()
                not in master.name.lower()
            ):
                continue

            if (
                master_category_filter.value
                and master_category_filter.value
                != "All"
                and master_category_filter.value.lower()
                not in master.specialization.lower()
            ):
                continue

            stat = stats[
                master.name
            ]

            rows.append(
                {
                    "name":
                        master.name,
                    "category":
                        master.specialization,
                    "bookings":
                        stat["bookings"],
                    "revenue":
                        f"${stat['revenue']:,.0f}",
                    "rating":
                        master.rating,
                }
            )

        rows.sort(
            key=lambda r:
                r["bookings"],
            reverse=True,
        )

        ui.label(
            "Master Performance"
        ).classes(
            "text-xl font-bold px-6 mb-2"
        )

        columns = [
            {
                "name": "name",
                "label": "Master",
                "field": "name",
                "align": "left",
            },
            {
                "name": "category",
                "label": "Category",
                "field": "category",
            },
            {
                "name": "bookings",
                "label": "Bookings",
                "field": "bookings",
            },
            {
                "name": "revenue",
                "label": "Revenue",
                "field": "revenue",
            },
            {
                "name": "rating",
                "label": "Rating",
                "field": "rating",
            },
        ]

        with ui.card().classes(
            "mx-6 mb-6 w-full rounded-2xl p-4"
        ):

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
            ).classes(
                "w-full"
            )

    master_performance_table()

    # =====================================================
    # Refresh
    # =====================================================

    def on_period_change() -> None:

        kpi_row.refresh()
        revenue_and_payment_charts.refresh()
        revenue_month_city_charts.refresh()
        masters_services_charts.refresh()
        status_clients_charts.refresh()
        hours_weekday_charts.refresh()
        ai_stats.refresh()
        master_performance_table.refresh()

    period_select.on_value_change(
        on_period_change
    )

    master_search_input.on(
        "keydown.enter",
        master_performance_table.refresh,
    )

    master_category_filter.on_value_change(
        master_performance_table.refresh
    )

    print(
        "[Analytics API] "
        f"{len(bookings)} bookings, "
        f"{len(clients)} clients, "
        f"{len(masters)} masters, "
        f"{len(services)} services, "
        f"{len(payments)} payments"
    )