from nicegui import ui
from pages.layout import add_navigation
from database import get_connection


@ui.page("/bookings")
def bookings_page() -> None:

    add_navigation(active="/bookings")

    ui.query("body").style("background:#F5F6FA")

    ui.label("Bookings").classes("text-3xl font-bold m-6")

    # helper functions for option loading
    def load_options() -> tuple[dict, dict, dict]:
        conn = get_connection()
        cursor = conn.cursor()
        clients = {
            r["client_name"]: r["client_id"]
            for r in cursor.execute(
                "SELECT client_id, client_name FROM clients ORDER BY client_name"
            ).fetchall()
        }
        masters = {
            r["master_name"]: r["master_id"]
            for r in cursor.execute(
                "SELECT master_id, master_name FROM masters ORDER BY master_name"
            ).fetchall()
        }
        services = {
            r["service_name"]: r["service_id"]
            for r in cursor.execute(
                "SELECT service_id, service_name FROM services ORDER BY service_name"
            ).fetchall()
        }
        conn.close()
        return clients, masters, services

    clients_options, masters_options, services_options = load_options()

    # toolbar
    with ui.row().classes("w-full px-6 gap-4 items-center"):

        search_input = (
            ui.input(placeholder="Search booking...")
            .props("outlined dense")
            .classes("w-80")
        )

        status_filter = ui.select(
            ["All", "Completed", "Cancelled", "No-show"],
            value="All",
            label="Status",
        ).classes("w-48")

        date_filter = (
            ui.input(placeholder="Date")
            .props("outlined dense type=date")
            .classes("w-48")
        )

        ui.space()

        # add booking dialog
        with ui.dialog() as add_dialog, ui.card().classes("p-4 gap-2 w-96"):
            ui.label("Add Booking").classes("text-lg font-bold")

            client_select = ui.select(
                list(clients_options.keys()), label="Client", with_input=True
            ).classes("w-full")
            master_select = ui.select(
                list(masters_options.keys()), label="Master", with_input=True
            ).classes("w-full")
            service_select = ui.select(
                list(services_options.keys()), label="Service", with_input=True
            ).classes("w-full")
            date_input = ui.input(label="Date").props("type=date").classes("w-full")
            time_input = ui.input(label="Time").props("type=time").classes("w-full")

            def save_new_booking() -> None:
                c_name = client_select.value
                m_name = master_select.value
                s_name = service_select.value
                d_val = date_input.value
                t_val = time_input.value

                if not (c_name and m_name and s_name and d_val and t_val):
                    ui.notify("Fill in all fields", color="negative")
                    return

                c_map, m_map, s_map = load_options()
                client_id = c_map.get(c_name)
                master_id = m_map.get(m_name)
                service_id = s_map.get(s_name)

                if not (client_id and master_id and service_id):
                    ui.notify("Invalid client, master, or service selection", color="negative")
                    return

                booking_datetime = f"{d_val} {t_val}:00"

                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO bookings (client_id, master_id, service_id, booking_datetime, status)
                    VALUES (?, ?, ?, ?, 'Completed')
                    """,
                    (client_id, master_id, service_id, booking_datetime),
                )
                conn.commit()
                conn.close()

                ui.notify("Booking added", color="positive")
                add_dialog.close()
                load_bookings()

            with ui.row().classes("justify-end gap-2 mt-2 w-full"):
                ui.button("Cancel", on_click=add_dialog.close).props("flat")
                ui.button("Save", on_click=save_new_booking).classes("bg-purple-600 text-white")

        ui.button("Add Booking", icon="event_available", on_click=add_dialog.open).classes(
            "bg-purple-600 text-white"
        )

    ui.separator().classes("my-4")

    # table configuration
    columns = [
        {"name": "id", "label": "ID", "field": "id", "align": "left"},
        {"name": "client", "label": "Client", "field": "client"},
        {"name": "master", "label": "Master", "field": "master"},
        {"name": "service", "label": "Service", "field": "service"},
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

    def load_bookings() -> None:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                b.booking_id AS id,
                c.client_name AS client,
                m.master_name AS master,
                s.service_name AS service,
                b.booking_datetime AS booking_datetime,
                s.base_price AS price,
                b.status AS status
            FROM bookings b
            JOIN clients c ON c.client_id = b.client_id
            JOIN masters m ON m.master_id = b.master_id
            JOIN services s ON s.service_id = b.service_id
            WHERE 1=1
        """
        params = []

        if search_input.value:
            query += " AND (c.client_name LIKE ? OR m.master_name LIKE ? OR s.service_name LIKE ?)"
            like = f"%{search_input.value}%"
            params.extend([like, like, like])

        if status_filter.value and status_filter.value != "All":
            query += " AND b.status = ?"
            params.append(status_filter.value)

        if date_filter.value:
            query += " AND DATE(b.booking_datetime) = ?"
            params.append(date_filter.value)

        query += " ORDER BY b.booking_datetime DESC LIMIT 200"

        rows = cursor.execute(query, params).fetchall()

        table.rows = [
            {
                "id": r["id"],
                "client": r["client"],
                "master": r["master"],
                "service": r["service"],
                "date": str(r["booking_datetime"])[:10] if r["booking_datetime"] else "",
                "time": str(r["booking_datetime"])[11:16] if r["booking_datetime"] else "",
                "price": f"${r['price']:,.0f}" if r["price"] is not None else "$0",
                "status": r["status"],
            }
            for r in rows
        ]
        table.selected.clear()
        table.update()

        conn.close()

    search_input.on("keydown.enter", load_bookings)
    status_filter.on_value_change(load_bookings)
    date_filter.on_value_change(load_bookings)

    load_bookings()

    ui.separator().classes("my-4")

    # row selection helper
    def get_selected() -> dict | None:
        if not table.selected:
            ui.notify("Select a booking first", color="warning")
            return None
        return table.selected[0]

    # dialog containers for action handlers
    with ui.dialog() as view_dialog, ui.card().classes("p-4 gap-1 w-96"):
        view_id_lbl = ui.label().classes("text-lg font-bold")
        view_client_lbl = ui.label()
        view_master_lbl = ui.label()
        view_service_lbl = ui.label()
        view_datetime_lbl = ui.label()
        view_price_lbl = ui.label()
        view_status_lbl = ui.label()
        ui.button("Close", on_click=view_dialog.close).classes("mt-2")

    with ui.dialog() as edit_dialog, ui.card().classes("p-4 gap-2 w-96"):
        edit_title_lbl = ui.label().classes("text-lg font-bold")
        date_edit = ui.input(label="Date").props("type=date").classes("w-full")
        time_edit = ui.input(label="Time").props("type=time").classes("w-full")
        status_edit = ui.select(
            ["Completed", "Cancelled", "No-show"], label="Status"
        ).classes("w-full")
        active_edit_id = {"id": None}

        def save_edit() -> None:
            if not active_edit_id["id"]:
                return
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE bookings SET booking_datetime = ?, status = ? WHERE booking_id = ?",
                (f"{date_edit.value} {time_edit.value}:00", status_edit.value, active_edit_id["id"]),
            )
            conn.commit()
            conn.close()
            ui.notify(f"Booking #{active_edit_id['id']} updated", color="positive")
            edit_dialog.close()
            load_bookings()

        with ui.row().classes("justify-end gap-2 mt-2 w-full"):
            ui.button("Cancel", on_click=edit_dialog.close).props("flat")
            ui.button("Save", on_click=save_edit).classes("bg-purple-600 text-white")

    with ui.dialog() as cancel_dialog, ui.card().classes("p-4 gap-2 w-80"):
        cancel_title_lbl = ui.label().classes("text-lg font-bold")
        cancel_info_lbl = ui.label().classes("text-sm text-gray-500")
        active_cancel_id = {"id": None}

        def confirm_cancel() -> None:
            if not active_cancel_id["id"]:
                return
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE bookings SET status = 'Cancelled' WHERE booking_id = ?",
                (active_cancel_id["id"],),
            )
            conn.commit()
            conn.close()
            ui.notify(f"Booking #{active_cancel_id['id']} cancelled", color="positive")
            cancel_dialog.close()
            load_bookings()

        with ui.row().classes("justify-end gap-2 mt-2 w-full"):
            ui.button("Back", on_click=cancel_dialog.close).props("flat")
            ui.button("Cancel Booking", on_click=confirm_cancel).props("color=orange")

    with ui.dialog() as delete_dialog, ui.card().classes("p-4 gap-2 w-80"):
        delete_title_lbl = ui.label().classes("text-lg font-bold")
        ui.label("This also removes any linked payment/review records if enforced by the DB.").classes(
            "text-sm text-gray-500"
        )
        active_delete_id = {"id": None}

        def confirm_delete() -> None:
            if not active_delete_id["id"]:
                return
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM bookings WHERE booking_id = ?", (active_delete_id["id"],))
                conn.commit()
                ui.notify(f"Booking #{active_delete_id['id']} deleted", color="positive")
                load_bookings()
            except Exception as e:
                ui.notify(f"Could not delete: {e}", color="negative")
            finally:
                conn.close()
            delete_dialog.close()

        with ui.row().classes("justify-end gap-2 mt-2 w-full"):
            ui.button("Cancel", on_click=delete_dialog.close).props("flat")
            ui.button("Delete", on_click=confirm_delete).props("color=red")

    # action button functions
    def view_booking() -> None:
        row = get_selected()
        if not row:
            return
        view_id_lbl.text = f"Booking #{row['id']}"
        view_client_lbl.text = f"Client: {row['client']}"
        view_master_lbl.text = f"Master: {row['master']}"
        view_service_lbl.text = f"Service: {row['service']}"
        view_datetime_lbl.text = f"Date: {row['date']} {row['time']}"
        view_price_lbl.text = f"Price: {row['price']}"
        view_status_lbl.text = f"Status: {row['status']}"
        view_dialog.open()

    def edit_booking() -> None:
        row = get_selected()
        if not row:
            return
        active_edit_id["id"] = row["id"]
        edit_title_lbl.text = f"Edit Booking #{row['id']}"
        date_edit.value = row["date"]
        time_edit.value = row["time"]
        status_edit.value = row["status"]
        edit_dialog.open()

    def cancel_booking() -> None:
        row = get_selected()
        if not row:
            return
        active_cancel_id["id"] = row["id"]
        cancel_title_lbl.text = f"Cancel booking #{row['id']}?"
        cancel_info_lbl.text = f"{row['client']} · {row['service']} · {row['date']} {row['time']}"
        cancel_dialog.open()

    def delete_booking() -> None:
        row = get_selected()
        if not row:
            return
        active_delete_id["id"] = row["id"]
        delete_title_lbl.text = f"Delete booking #{row['id']}?"
        delete_dialog.open()

    # action bar
    with ui.row().classes("gap-3 px-6"):
        ui.button("View", icon="visibility", on_click=view_booking)
        ui.button("Edit", icon="edit", on_click=edit_booking)
        ui.button("Cancel", icon="event_busy", on_click=cancel_booking).props("color=orange")
        ui.button("Delete", icon="delete", on_click=delete_booking).props("color=red")