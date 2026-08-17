from nicegui import ui
from pages.layout import add_navigation
from database import get_connection


@ui.page("/services")
def services_page() -> None:

    add_navigation(active="/services")

    ui.query("body").style("background:#F5F6FA")

    ui.label("Services").classes("text-3xl font-bold m-6")

    # --------------------
    # Toolbar
    # --------------------

    with ui.row().classes("w-full px-6 gap-4 items-center"):

        search_input = ui.input(
            placeholder="Search service..."
        ).props("outlined dense").classes("w-80")

        category_filter = ui.select(
            ["All", "Barber", "Brows", "Cosmetology", "Hair", "Laser",
             "Lashes", "Makeup", "Nails", "SPA", "Skincare"],
            value="All",
            label="Category",
        ).classes("w-56")

        ui.space()

        def add_service(name: str, category: str, duration: int, price: float) -> None:
            if not name.strip():
                ui.notify("Enter service name", color="negative")
                return
            if duration <= 0 or price <= 0:
                ui.notify("Duration and price must be positive", color="negative")
                return

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO services (service_name, category, duration_min, base_price)
                VALUES (?, ?, ?, ?)
                """,
                (name.strip(), category, duration, price),
            )
            conn.commit()
            conn.close()

            ui.notify(f"Service '{name}' added", color="positive")
            add_dialog.close()
            load_services()

        with ui.dialog() as add_dialog, ui.card().classes("p-4 gap-2 w-96"):
            ui.label("Add Service").classes("text-lg font-bold")

            name_input = ui.input(label="Service name").classes("w-full")
            category_input = ui.select(
                ["Barber", "Brows", "Cosmetology", "Hair", "Laser",
                 "Lashes", "Makeup", "Nails", "SPA", "Skincare"],
                label="Category",
                value="Hair",
            ).classes("w-full")
            duration_input = ui.number(label="Duration (min)", value=60, min=5, step=5).classes("w-full")
            price_input = ui.number(label="Price ($)", value=30, min=1, step=1).classes("w-full")

            with ui.row().classes("justify-end gap-2 mt-2 w-full"):
                ui.button("Cancel", on_click=add_dialog.close).props("flat")
                ui.button(
                    "Save",
                    on_click=lambda: add_service(
                        name_input.value or "",
                        category_input.value,
                        int(duration_input.value or 0),
                        float(price_input.value or 0),
                    ),
                ).classes("bg-purple-600 text-white")

        ui.button("Add Service", icon="add", on_click=add_dialog.open).classes(
            "bg-purple-600 text-white"
        )

    ui.separator().classes("my-4")

    # --------------------
    # Table
    # --------------------

    columns = [
        {"name": "name", "label": "Service", "field": "name", "align": "left"},
        {"name": "category", "label": "Category", "field": "category"},
        {"name": "duration", "label": "Duration", "field": "duration"},
        {"name": "price", "label": "Price", "field": "price"},
        {"name": "masters", "label": "Master(s)", "field": "masters"},
        {"name": "bookings", "label": "Bookings", "field": "bookings"},
    ]

    table = ui.table(
        columns=columns,
        rows=[],
        row_key="name",
        pagination=10,
        selection="single",
    ).classes("w-full px-6")

    def load_services() -> None:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                s.service_id AS service_id,
                s.service_name AS name,
                s.category AS category,
                s.duration_min AS duration_min,
                s.base_price AS price
            FROM services s
            WHERE 1=1
        """
        params = []

        if search_input.value:
            query += " AND s.service_name LIKE ?"
            params.append(f"%{search_input.value}%")

        if category_filter.value and category_filter.value != "All":
            query += " AND s.category = ?"
            params.append(category_filter.value)

        query += " ORDER BY s.service_name"

        services = cursor.execute(query, params).fetchall()

        result = []
        for s in services:
            masters = cursor.execute(
                """
                SELECT DISTINCT m.master_name
                FROM bookings b
                JOIN masters m ON m.master_id = b.master_id
                WHERE b.service_id = ?
                LIMIT 3
                """,
                (s["service_id"],),
            ).fetchall()

            bookings_count = cursor.execute(
                "SELECT COUNT(*) AS total FROM bookings WHERE service_id = ?",
                (s["service_id"],),
            ).fetchone()["total"]

            result.append(
                {
                    "name": s["name"],
                    "category": s["category"],
                    "duration": f"{s['duration_min']} min",
                    "price": f"${s['price']:,.0f}",
                    "masters": ", ".join(m["master_name"] for m in masters) or "—",
                    "bookings": bookings_count,
                }
            )

        table.rows = result
        table.update()

        conn.close()

    search_input.on("keydown.enter", load_services)
    category_filter.on_value_change(load_services)

    load_services()

    ui.separator().classes("my-4")

    # --------------------
    # Actions
    # --------------------

    with ui.row().classes("gap-3 px-6"):

        def get_selected() -> dict | None:
            if not table.selected:
                ui.notify("Select a service first", color="warning")
                return None
            return table.selected[0]

        def view_service() -> None:
            row = get_selected()
            if not row:
                return
            with ui.dialog() as view_dialog, ui.card().classes("p-4 gap-1 w-96"):
                ui.label(row["name"]).classes("text-lg font-bold")
                ui.label(f"Category: {row['category']}")
                ui.label(f"Duration: {row['duration']}")
                ui.label(f"Price: {row['price']}")
                ui.label(f"Master(s): {row['masters']}")
                ui.label(f"Bookings: {row['bookings']}")
                ui.button("Close", on_click=view_dialog.close).classes("mt-2")
            view_dialog.open()

        def edit_service() -> None:
            row = get_selected()
            if not row:
                return

            def save_edit(new_category: str, new_duration: int, new_price: float) -> None:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE services SET category = ?, duration_min = ?, base_price = ? WHERE service_name = ?",
                    (new_category, new_duration, new_price, row["name"]),
                )
                conn.commit()
                conn.close()
                ui.notify(f"Updated {row['name']}", color="positive")
                edit_dialog.close()
                load_services()

            with ui.dialog() as edit_dialog, ui.card().classes("p-4 gap-2 w-96"):
                ui.label(f"Edit {row['name']}").classes("text-lg font-bold")

                category_edit = ui.select(
                    ["Barber", "Brows", "Cosmetology", "Hair", "Laser",
                     "Lashes", "Makeup", "Nails", "SPA", "Skincare"],
                    label="Category",
                    value=row["category"],
                ).classes("w-full")
                duration_edit = ui.number(
                    label="Duration (min)", value=int(row["duration"].split()[0]), min=5, step=5
                ).classes("w-full")
                price_edit = ui.number(
                    label="Price ($)", value=float(row["price"].replace("$", "").replace(",", "")), min=1, step=1
                ).classes("w-full")

                with ui.row().classes("justify-end gap-2 mt-2 w-full"):
                    ui.button("Cancel", on_click=edit_dialog.close).props("flat")
                    ui.button(
                        "Save",
                        on_click=lambda: save_edit(
                            category_edit.value,
                            int(duration_edit.value or 0),
                            float(price_edit.value or 0),
                        ),
                    ).classes("bg-purple-600 text-white")

            edit_dialog.open()

        def deactivate_service() -> None:
            row = get_selected()
            if not row:
                return
            ui.notify(
                f"No active/inactive column in services table yet for '{row['name']}'",
                color="info",
            )

        def delete_service() -> None:
            row = get_selected()
            if not row:
                return

            def confirm_delete() -> None:
                conn = get_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute("DELETE FROM services WHERE service_name = ?", (row["name"],))
                    conn.commit()
                    ui.notify(f"'{row['name']}' deleted", color="positive")
                    load_services()
                except Exception as e:
                    ui.notify(f"Could not delete: {e}", color="negative")
                finally:
                    conn.close()
                delete_dialog.close()

            with ui.dialog() as delete_dialog, ui.card().classes("p-4 gap-2 w-80"):
                ui.label(f"Delete '{row['name']}'?").classes("text-lg font-bold")
                ui.label(
                    f"This service has {row['bookings']} booking(s) linked to it. "
                    "Deleting may fail if the database enforces foreign keys."
                ).classes("text-sm text-gray-500")
                with ui.row().classes("justify-end gap-2 mt-2 w-full"):
                    ui.button("Cancel", on_click=delete_dialog.close).props("flat")
                    ui.button("Delete", on_click=confirm_delete).props("color=red")

            delete_dialog.open()

        ui.button("View", icon="visibility", on_click=view_service)
        ui.button("Edit", icon="edit", on_click=edit_service)
        ui.button("Deactivate", icon="block", on_click=deactivate_service).props("color=orange")
        ui.button("Delete", icon="delete", on_click=delete_service).props("color=red")