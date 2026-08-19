from nicegui import ui

from pages.layout import add_navigation
from data_access.dashboard import get_dashboard_data


def _pct_change(
    current: float,
    previous: float
) -> str:

    if previous == 0:
        return "+100%" if current > 0 else "0%"

    change = (
        (current - previous)
        / previous
        * 100
    )

    sign = "+" if change >= 0 else ""

    return f"{sign}{change:.1f}%"


def _kpi_card(
    title: str,
    value: str,
    change: str,
    icon: str,
    color: str
) -> None:

    is_positive = (
        change.startswith("+")
        or change == "0%"
    )

    change_color = (
        "text-green-600"
        if is_positive
        else "text-gray-500"
    )

    triangle = "▲" if is_positive else "▼"

    change_value = change.lstrip("+-")

    with ui.card().classes(
        "p-5 flex-1 min-w-[220px] "
        "rounded-2xl shadow-sm"
    ):

        ui.label(title).classes(
            "text-xs text-gray-500 mb-0"
        )

        with ui.row().classes(
            "items-center justify-between w-full"
        ):

            with ui.row().classes(
                "items-center gap-3"
            ):

                ui.icon(icon).classes(
                    f"text-2xl {color}"
                )

                ui.label(value).classes(
                    "text-2xl font-bold"
                )

            ui.label(
                f"{triangle} {change_value}"
            ).classes(
                f"text-sm font-medium {change_color}"
            )


def _stat_card(
    title: str,
    value: str,
    icon: str,
    color: str
) -> None:

    with ui.card().classes(
        "p-5 flex-1 min-w-[220px] "
        "rounded-2xl shadow-sm"
    ):

        ui.label(title).classes(
            "text-xs text-gray-500 mb-0"
        )

        with ui.row().classes(
            "items-center gap-3"
        ):

            ui.icon(icon).classes(
                f"text-2xl {color}"
            )

            ui.label(value).classes(
                "text-2xl font-bold"
            )


@ui.page("/dashboard")
def dashboard_page() -> None:

    add_navigation(active="/dashboard")

    ui.query("body").style(
        "background:#F5F6FA"
    )

    ui.label("Dashboard").classes(
        "text-3xl font-bold m-6 mb-1"
    )

    ui.label(
        "Operational overview — what's happening right now"
    ).classes(
        "text-sm text-gray-500 px-6 mb-4"
    )

    try:

        data = get_dashboard_data()

    except Exception as e:

        print(
            f"[Dashboard API Error]: {e}"
        )

        ui.notify(
            f"Could not load dashboard: {e}",
            color="negative",
        )

        return

    print(
        "[Dashboard API] "
        f"{data.bookings_current} bookings / "
        f"{data.clients_current} clients"
    )

    # =====================================================
    # KPI
    # =====================================================

    with ui.element("div").classes(
        "grid gap-4 px-6 w-full "
        "grid-cols-1 md:grid-cols-2 xl:grid-cols-4"
    ):

        _kpi_card(
            "Booking Value (30d)",
            f"${data.revenue_current / 1000:.1f}K",
            _pct_change(
                data.revenue_current,
                data.revenue_previous,
            ),
            "payments",
            "text-purple-600",
        )

        _kpi_card(
            "Total Bookings (30d)",
            str(data.bookings_current),
            _pct_change(
                data.bookings_current,
                data.bookings_previous,
            ),
            "event",
            "text-purple-600",
        )

        _kpi_card(
            "New Clients (30d)",
            str(data.clients_current),
            _pct_change(
                data.clients_current,
                data.clients_previous,
            ),
            "groups",
            "text-purple-600",
        )

        _kpi_card(
            "Active Masters (30d)",
            str(data.masters_current),
            _pct_change(
                data.masters_current,
                data.masters_previous,
            ),
            "badge",
            "text-purple-600",
        )

    ui.separator().classes("my-5")

    # =====================================================
    # Today
    # =====================================================

    ui.label("Today").classes(
        "text-lg font-bold px-6 mb-2"
    )

    with ui.element("div").classes(
        "grid gap-4 px-6 w-full "
        "grid-cols-1 md:grid-cols-2 xl:grid-cols-4"
    ):

        _stat_card(
            "Bookings Today",
            str(data.bookings_today),
            "calendar_today",
            "text-purple-600",
        )

        _stat_card(
            "Completed Today",
            str(data.completed_today),
            "check_circle",
            "text-green-600",
        )

        _stat_card(
            "Cancelled Today",
            str(data.cancelled_today),
            "cancel",
            "text-gray-600",
        )

        _stat_card(
            "No-show Today",
            str(data.noshow_today),
            "person_off",
            "text-gray-600",
        )

    ui.separator().classes("my-5")

    # =====================================================
    # Recent + schedule
    # =====================================================

    with ui.row().classes(
        "px-6 gap-4 w-full flex-wrap items-stretch"
    ):

        with ui.card().classes(
            "p-4 flex-1 min-w-[650px] "
            "h-[500px] rounded-2xl shadow-sm"
        ).props("flat"):

            ui.label(
                "Recent Bookings"
            ).classes(
                "text-lg font-semibold mb-2"
            )

            columns = [
                {
                    "name": "id",
                    "label": "ID",
                    "field": "id",
                },
                {
                    "name": "client",
                    "label": "Client",
                    "field": "client",
                },
                {
                    "name": "master",
                    "label": "Master",
                    "field": "master",
                },
                {
                    "name": "datetime",
                    "label": "Date / Time",
                    "field": "datetime",
                },
                {
                    "name": "status",
                    "label": "Status",
                    "field": "status",
                },
            ]

            rows = [
                {
                    "id": b.id,
                    "client": b.client,
                    "master": b.master,
                    "datetime": b.date_time,
                    "status": b.status,
                }
                for b in data.recent_bookings
            ]

            ui.table(
                columns=columns,
                rows=rows,
                row_key="id",
                pagination=12,
            ).props(
                'dense flat separator=horizontal '
                ':rows-per-page-options="[12]"'
            ).classes("w-full")

        with ui.card().classes(
            "p-4 flex-1 min-w-[500px] "
            "h-[500px] rounded-2xl shadow-sm"
        ).props("flat"):

            ui.label(
                "Today's Schedule"
            ).classes(
                "text-lg font-semibold mb-2"
            )

            with ui.scroll_area().classes(
                "w-full h-[430px]"
            ):

                if not data.today_schedule:

                    ui.label(
                        "No bookings scheduled for today."
                    ).classes(
                        "text-sm text-gray-500"
                    )

                for booking in data.today_schedule:

                    time_label = ""

                    if " " in booking.date_time:
                        time_label = (
                            booking.date_time
                            .split(" ", 1)[1][:5]
                        )

                    ui.separator()

                    with ui.row().classes(
                        "items-center justify-between "
                        "w-full py-1"
                    ):

                        with ui.column().classes("gap-0"):

                            ui.label(
                                f"{time_label} — "
                                f"{booking.client}"
                            ).classes(
                                "font-medium text-sm"
                            )

                            ui.label(
                                f"{booking.service} · "
                                f"{booking.master}"
                            ).classes(
                                "text-xs text-gray-500"
                            )

                        ui.label(
                            booking.status
                        ).classes(
                            "text-xs text-gray-500"
                        )

    ui.separator().classes("my-5")

    # =====================================================
    # Top masters + alerts
    # =====================================================

    with ui.row().classes(
        "px-6 gap-4 w-full flex-wrap items-stretch"
    ):

        with ui.card().classes(
            "flex-1 min-w-[500px] "
            "p-4 rounded-2xl shadow-sm"
        ):

            ui.label(
                "Top Masters Today"
            ).classes(
                "text-lg font-semibold mb-2"
            )

            if data.top_masters:

                medals = ["🥇", "🥈", "🥉"]

                with ui.row().classes(
                    "w-full gap-3"
                ):

                    for i, master in enumerate(
                        data.top_masters
                    ):

                        with ui.card().classes(
                            "flex-1 p-3 "
                            "rounded-xl shadow-sm"
                        ):

                            ui.label(
                                medals[i]
                            ).classes("text-2xl")

                            ui.label(
                                master.name
                            ).classes(
                                "font-semibold text-sm"
                            )

                            ui.label(
                                f"⭐ {master.rating:.1f}"
                            ).classes(
                                "text-xs text-gray-500"
                            )

                            ui.label(
                                f"{master.bookings} bookings"
                            ).classes(
                                "text-xs text-gray-500"
                            )

                            ui.label(
                                f"${master.revenue:,.0f}"
                            ).classes(
                                "text-lg font-bold "
                                "text-purple-600"
                            )

            else:

                ui.label(
                    "No bookings today yet."
                ).classes(
                    "text-sm text-gray-500"
                )

        with ui.card().classes(
            "flex-1 min-w-[350px] "
            "p-4 rounded-2xl shadow-sm"
        ):

            ui.label(
                "Notifications & Alerts"
            ).classes(
                "text-lg font-semibold mb-2"
            )

            alerts = [
                (
                    f"{data.new_reviews_today} "
                    "new review(s) today",
                    "rate_review",
                    "text-blue-600",
                ),
                (
                    f"{data.low_ratings_today} "
                    "low rating(s) (≤2★) today",
                    "warning",
                    "text-red-600",
                ),
                (
                    f"{data.ai_searches_today} "
                    "new AI searches today",
                    "auto_awesome",
                    "text-purple-600",
                ),
            ]

            for text, icon, color in alerts:

                with ui.row().classes(
                    "items-center gap-3 py-1"
                ):

                    ui.icon(icon).classes(
                        f"text-xl {color}"
                    )

                    ui.label(text).classes(
                        "text-sm"
                    )