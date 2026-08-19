from nicegui import ui

from pages.layout import add_navigation
from data_access.bookings import get_bookings


@ui.page("/bookings")
def bookings_page() -> None:

    add_navigation(active="/bookings")

    ui.query("body").style("background:#F5F6FA")

    ui.label("Bookings").classes("text-3xl font-bold m-6")

    # -----------------------------
    # Toolbar
    # -----------------------------

    with ui.row().classes("w-full px-6 gap-4 items-center"):

        search_input = (
            ui.input(placeholder="Search booking...")
            .props("outlined dense")
            .classes("w-80")
        )

        status_filter = ui.select(
            ["All", "Pending", "Confirmed", "Completed", "Cancelled", "No-show"],
            value="All",
            label="Status",
        ).classes("w-48")

        date_filter = (
            ui.input(placeholder="Date")
            .props("outlined dense type=date")
            .classes("w-48")
        )

        ui.space()

        # Поки POST endpoint не підключений
        ui.button(
            "Add Booking",
            icon="event_available",
            on_click=lambda: ui.notify(
                "Adding bookings via API is not connected yet",
                color="warning",
            ),
        ).classes("bg-purple-600 text-white")

    ui.separator().classes("my-4")

    # -----------------------------
    # Table
    # -----------------------------

    columns = [
        {"name": "id", "label": "ID", "field": "id", "align": "left"},
        {"name": "client", "label": "Client", "field": "client"},
        {"name": "master", "label": "Master", "field": "master"},
        {"name": "service", "label": "Service", "field": "service"},
        {"name": "salon", "label": "Salon", "field": "salon"},
        {"name": "date", "label": "Date", "field": "date"},
        {"name": "time", "label": "Time", "field": "time"},
        {"name": "price", "label": "Price", "field": "price"},
        {"name": "status", "label": "Status", "field": "status"},
    ]

    table = ui.table(
        columns=columns,
        rows=[],
        row_key="id",
        pagination=10,
        selection="single",
    ).classes("w-full px-6")

    # -----------------------------
    # Load bookings FROM API
    # -----------------------------

    def load_bookings() -> None:

        try:
            bookings = get_bookings(
                search=search_input.value or "",
                status=status_filter.value or "All",
            )
        except Exception as e:
            print(f"[Bookings Page Error]: {e}")
            ui.notify(
                f"Could not load bookings: {e}",
                color="negative",
            )
            table.rows = []
            table.update()
            return

        rows = []

        for booking in bookings:

            date_time = booking.date_time or ""

            if "T" in date_time:
                date_part, time_part = date_time.split("T", 1)
            elif " " in date_time:
                date_part, time_part = date_time.split(" ", 1)
            else:
                date_part = date_time
                time_part = ""

            time_part = time_part[:5]

            # Date filter
            if date_filter.value:
                if date_part != date_filter.value:
                    continue

            rows.append(
                {
                    "id": booking.id,
                    "client": booking.client_name,
                    "master": booking.master_name,
                    "service": booking.service_name,
                    "salon": booking.salon_name,
                    "date": date_part,
                    "time": time_part,
                    "price": f"${booking.price:,.0f}",
                    "status": booking.status,
                }
            )

        table.rows = rows
        table.selected.clear()
        table.update()

        print(f"[Bookings API] Loaded {len(rows)} bookings")

    search_input.on("keydown.enter", load_bookings)
    status_filter.on_value_change(load_bookings)
    date_filter.on_value_change(load_bookings)

    load_bookings()

    ui.separator().classes("my-4")

    # -----------------------------
    # Selected booking
    # -----------------------------

    def get_selected() -> dict | None:

        if not table.selected:
            ui.notify(
                "Select a booking first",
                color="warning",
            )
            return None

        return table.selected[0]

    # -----------------------------
    # View dialog
    # -----------------------------

    with ui.dialog() as view_dialog, ui.card().classes(
        "p-4 gap-1 w-96"
    ):

        view_id_lbl = ui.label().classes("text-lg font-bold")
        view_client_lbl = ui.label()
        view_master_lbl = ui.label()
        view_service_lbl = ui.label()
        view_salon_lbl = ui.label()
        view_datetime_lbl = ui.label()
        view_price_lbl = ui.label()
        view_status_lbl = ui.label()

        ui.button(
            "Close",
            on_click=view_dialog.close,
        ).classes("mt-2")

    def view_booking() -> None:

        row = get_selected()

        if not row:
            return

        view_id_lbl.text = f"Booking #{row['id']}"
        view_client_lbl.text = f"Client: {row['client']}"
        view_master_lbl.text = f"Master: {row['master']}"
        view_service_lbl.text = f"Service: {row['service']}"
        view_salon_lbl.text = f"Salon: {row['salon']}"

        view_datetime_lbl.text = (
            f"Date: {row['date']} {row['time']}"
        )

        view_price_lbl.text = f"Price: {row['price']}"
        view_status_lbl.text = f"Status: {row['status']}"

        view_dialog.open()

    # -----------------------------
    # API actions not connected yet
    # -----------------------------

    def edit_booking() -> None:

        row = get_selected()

        if not row:
            return

        ui.notify(
            "Editing via API is not connected yet",
            color="warning",
        )

    def cancel_booking() -> None:

        row = get_selected()

        if not row:
            return

        ui.notify(
            "Cancelling via API is not connected yet",
            color="warning",
        )

    def delete_booking() -> None:

        row = get_selected()

        if not row:
            return

        ui.notify(
            "Deleting via API is not connected yet",
            color="warning",
        )

    # -----------------------------
    # Action bar
    # -----------------------------

    with ui.row().classes("gap-3 px-6"):

        ui.button(
            "View",
            icon="visibility",
            on_click=view_booking,
        )

        ui.button(
            "Edit",
            icon="edit",
            on_click=edit_booking,
        )

        ui.button(
            "Cancel",
            icon="event_busy",
            on_click=cancel_booking,
        ).props("color=orange")

        ui.button(
            "Delete",
            icon="delete",
            on_click=delete_booking,
        ).props("color=red")