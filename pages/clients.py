from nicegui import ui
from pages.layout import add_navigation
from database import get_connection
from data_access.clients import get_clients


@ui.page("/clients")
def clients_page():

    add_navigation(active="/clients")

    ui.query("body").style("background:#F5F6FA")

    ui.label("Clients").classes("text-3xl font-bold m-6")

    # toolbar
    with ui.row().classes("w-full px-6 gap-4 items-center"):

        search_input = (
            ui.input(placeholder="Search client...")
            .props("outlined dense")
            .classes("w-80")
        )

        status_filter = ui.select(
            ["All", "Active", "Inactive"],
            value="All",
            label="Status",
        ).classes("w-48")

        ui.space()

        def add_client(name: str, city: str, channel: str) -> None:
            if not name.strip():
                ui.notify("Enter client name", color="negative")
                return

            conn = get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO clients (client_name, city, registration_date, acquisition_channel)
                    VALUES (?, ?, DATE('now'), ?)
                    """,
                    (name.strip(), city.strip() or None, channel),
                )
                conn.commit()
            finally:
                conn.close()

            ui.notify(f"Client '{name}' added", color="positive")
            add_dialog.close()
            load_clients()

        with ui.dialog() as add_dialog, ui.card().classes("p-4 gap-2 w-96"):
            ui.label("Add Client").classes("text-lg font-bold")

            new_name_input = ui.input(label="Full name").classes("w-full")
            new_city_input = ui.input(label="City").classes("w-full")
            new_channel_input = ui.select(
                ["Instagram", "Google", "Referral", "Website", "Walk-in", "Other"],
                label="Acquisition channel",
                value="Other",
            ).classes("w-full")

            with ui.row().classes("justify-end gap-2 mt-2 w-full"):
                ui.button("Cancel", on_click=add_dialog.close).props("flat")
                ui.button(
                    "Save",
                    on_click=lambda: add_client(
                        new_name_input.value or "",
                        new_city_input.value or "",
                        new_channel_input.value,
                    ),
                ).classes("bg-purple-600 text-white")

        ui.button("Add Client", icon="person_add", on_click=add_dialog.open).classes(
            "bg-purple-600 text-white"
        )

    ui.separator().classes("my-4")

    # table configuration
    columns = [
        {"name": "name", "label": "Name", "field": "name", "align": "left"},
        {"name": "city", "label": "City", "field": "city"},
        {"name": "acquisition_channel", "label": "Source", "field": "acquisition_channel"},
        {"name": "bookings", "label": "Bookings", "field": "bookings"},
        {"name": "spent", "label": "Spent", "field": "spent"},
        {"name": "last_visit", "label": "Last Visit", "field": "last_visit"},
        {"name": "status", "label": "Status", "field": "status"},
    ]

    table = ui.table(
        columns=columns,
        rows=[],
        row_key="client_id",
        pagination=10,
        selection="single",
    ).classes("w-full px-6")

    def load_clients() -> None:
        try:
            rows = get_clients(search_input.value, status_filter.value)
        except NotImplementedError:
            ui.notify(
                "Clients list isn't available from the backend API yet "
                "(waiting on SCRUM-187) — showing empty list.",
                color="warning",
            )
            table.rows = []
            table.update()
            return

        table.rows = [
            {
                "client_id": r.id,
                "name": r.name,
                "city": r.city,
                "acquisition_channel": r.acquisition_channel,
                "bookings": r.bookings,
                "spent": f"${r.spent:,.0f}",
                "last_visit": r.last_visit,
                "status": r.status,
            }
            for r in rows
        ]
        table.update()

    search_input.on("keydown.enter", load_clients)
    status_filter.on_value_change(load_clients)

    load_clients()

    ui.separator().classes("my-4")

    # actions
    with ui.row().classes("gap-3 px-6 mt-4"):

        def get_selected() -> dict | None:
            if not table.selected:
                ui.notify("Select a client first", color="warning")
                return None
            return table.selected[0]

        def view_client() -> None:
            row = get_selected()
            if not row:
                return
            with ui.dialog() as view_dialog, ui.card().classes("p-4 gap-1 w-96"):
                ui.label(row["name"]).classes("text-lg font-bold")
                ui.label(f"City: {row['city']}")
                ui.label(f"Source: {row['acquisition_channel']}")
                ui.label(f"Bookings: {row['bookings']}")
                ui.label(f"Spent: {row['spent']}")
                ui.label(f"Last visit: {row['last_visit']}")
                ui.label(f"Status: {row['status']}")
                ui.button("Close", on_click=view_dialog.close).classes("mt-2")
            view_dialog.open()

        def edit_client() -> None:
            row = get_selected()
            if not row:
                return

            def save_edit(new_city: str, new_channel: str) -> None:
                conn = get_connection()
                try:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE clients SET city = ?, acquisition_channel = ? WHERE client_id = ?",
                        (new_city.strip() or None, new_channel, row["client_id"]),
                    )
                    conn.commit()
                finally:
                    conn.close()
                ui.notify(f"Updated {row['name']}", color="positive")
                edit_dialog.close()
                load_clients()

            with ui.dialog() as edit_dialog, ui.card().classes("p-4 gap-2 w-96"):
                ui.label(f"Edit {row['name']}").classes("text-lg font-bold")

                city_input = ui.input(label="City", value=row["city"]).classes("w-full")
                channel_input = ui.select(
                    ["Instagram", "Google", "Referral", "Website", "Walk-in", "Other"],
                    label="Acquisition channel",
                    value=row["acquisition_channel"],
                ).classes("w-full")

                with ui.row().classes("justify-end gap-2 mt-2 w-full"):
                    ui.button("Cancel", on_click=edit_dialog.close).props("flat")
                    ui.button(
                        "Save",
                        on_click=lambda: save_edit(city_input.value or "", channel_input.value),
                    ).classes("bg-purple-600 text-white")

            edit_dialog.open()

        def show_bookings() -> None:
            row = get_selected()
            if not row:
                return

            conn = get_connection()
            try:
                cursor = conn.cursor()
                bookings = cursor.execute(
                    """
                    SELECT
                        b.booking_id AS id,
                        m.master_name AS master,
                        s.service_name AS service,
                        b.booking_datetime AS booking_datetime,
                        b.status AS status
                    FROM bookings b
                    JOIN masters m ON m.master_id = b.master_id
                    JOIN services s ON s.service_id = b.service_id
                    WHERE b.client_id = ?
                    ORDER BY b.booking_datetime DESC
                    LIMIT 50
                    """,
                    (row["client_id"],),
                ).fetchall()
            finally:
                conn.close()

            with ui.dialog() as bookings_dialog, ui.card().classes("p-4 w-[600px]"):
                ui.label(f"Bookings — {row['name']}").classes("text-lg font-bold mb-2")

                booking_columns = [
                    {"name": "id", "label": "ID", "field": "id", "align": "left"},
                    {"name": "master", "label": "Master", "field": "master"},
                    {"name": "service", "label": "Service", "field": "service"},
                    {"name": "date", "label": "Date", "field": "date"},
                    {"name": "status", "label": "Status", "field": "status"},
                ]
                booking_rows = [
                    {
                        "id": b["id"],
                        "master": b["master"],
                        "service": b["service"],
                        "date": b["booking_datetime"][:16].replace("T", " "),
                        "status": b["status"],
                    }
                    for b in bookings
                ]

                ui.table(columns=booking_columns, rows=booking_rows, row_key="id", pagination=10).classes(
                    "w-full"
                )
                ui.button("Close", on_click=bookings_dialog.close).classes("mt-2")

            bookings_dialog.open()

        def delete_client() -> None:
            row = get_selected()
            if not row:
                return

            def confirm_delete() -> None:
                conn = get_connection()
                try:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM clients WHERE client_id = ?", (row["client_id"],))
                    conn.commit()
                    ui.notify(f"{row['name']} deleted", color="positive")
                    load_clients()
                except Exception as e:
                    ui.notify(f"Could not delete: {e}", color="negative")
                finally:
                    conn.close()
                delete_dialog.close()

            with ui.dialog() as delete_dialog, ui.card().classes("p-4 gap-2 w-80"):
                ui.label(f"Delete {row['name']}?").classes("text-lg font-bold")
                ui.label(
                    f"This client has {row['bookings']} booking(s). Deleting may fail or "
                    "leave orphaned booking records if the database enforces foreign keys."
                ).classes("text-sm text-gray-500")
                with ui.row().classes("justify-end gap-2 mt-2 w-full"):
                    ui.button("Cancel", on_click=delete_dialog.close).props("flat")
                    ui.button("Delete", on_click=confirm_delete).props("color=red")

            delete_dialog.open()

        ui.button("View", icon="visibility", on_click=view_client)
        ui.button("Edit", icon="edit", on_click=edit_client)
        ui.button("Bookings", icon="event", on_click=show_bookings)
        ui.button("Delete", icon="delete", on_click=delete_client).props("color=red")