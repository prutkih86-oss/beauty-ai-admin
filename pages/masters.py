from nicegui import ui
from pages.layout import add_navigation
from data_access.masters import get_masters, add_master


@ui.page("/masters")
def masters_page():

    add_navigation(active="/masters")

    ui.query("body").style("background:#F5F6FA")

    ui.label("Masters").classes("text-3xl font-bold m-6")

    # --------------------
    # Toolbar
    # --------------------

    with ui.row().classes("w-full px-6 gap-4 items-center"):

        search_input = ui.input(
            placeholder="Search master..."
        ).props("outlined dense").classes("w-80")

        category_filter = ui.select(
            ["All", "Hair", "Barber", "Makeup", "Nails", "Brows", "Lashes",
             "Cosmetology", "Laser", "SPA", "Skincare"],
            value="All",
            label="Specialization",
        ).classes("w-56")

        def add_master_dialog_submit(
            name: str, specialization: str, city: str, address: str, is_solo: bool
        ) -> None:
            if not name.strip():
                ui.notify("Enter master name", color="negative")
                return

            add_master(name, specialization, city, address, is_solo)
            ui.notify(f"Master '{name}' added", color="positive")
            dialog.close()
            load_masters()

        with ui.dialog() as dialog, ui.card().classes("p-4 gap-2 w-96"):
            ui.label("Add Master").classes("text-lg font-bold")

            name_input = ui.input(label="Full name").classes("w-full")
            specialization_input = ui.select(
                ["Hair", "Barber", "Makeup", "Nails", "Brows", "Lashes",
                 "Cosmetology", "Laser", "SPA", "Skincare"],
                label="Specialization",
                value="Hair",
            ).classes("w-full")
            city_input = ui.input(label="City").classes("w-full")
            address_input = ui.input(label="Address").classes("w-full")
            solo_switch = ui.switch("Solo master (not tied to a salon)")

            with ui.row().classes("justify-end gap-2 mt-2 w-full"):
                ui.button("Cancel", on_click=dialog.close).props("flat")
                ui.button(
                    "Save",
                    on_click=lambda: add_master_dialog_submit(
                        name_input.value or "",
                        specialization_input.value,
                        city_input.value or "",
                        address_input.value or "",
                        solo_switch.value,
                    ),
                ).classes("bg-purple-600 text-white")

        ui.space()

        ui.button("Add Master", icon="add", on_click=dialog.open).classes(
            "bg-purple-600 text-white"
        )

    ui.separator().classes("my-4")

    # --------------------
    # Table
    # --------------------

    columns = [
        {"name": "name", "label": "Name", "field": "name", "align": "left"},
        {"name": "specialization", "label": "Specialization", "field": "specialization"},
        {"name": "rating", "label": "Rating", "field": "rating"},
        {"name": "city", "label": "City", "field": "city"},
        {"name": "bookings", "label": "Bookings", "field": "bookings"},
        {"name": "revenue", "label": "Revenue", "field": "revenue"},
        {"name": "is_solo", "label": "Solo", "field": "is_solo"},
    ]

    table = ui.table(
        columns=columns,
        rows=[],
        row_key="name",
        pagination=10,
        selection="single",
    ).classes("w-full px-6")

    def load_masters() -> None:
        rows = get_masters(search_input.value, category_filter.value)

        table.rows = [
            {
                "name": r.name,
                "specialization": r.specialization,
                "rating": r.rating,
                "city": r.city,
                "bookings": r.bookings,
                "revenue": f"${r.revenue:,.0f}",
                "is_solo": "Solo" if r.is_solo else "Salon",
            }
            for r in rows
        ]
        table.update()

    search_input.on("keydown.enter", load_masters)
    category_filter.on_value_change(load_masters)

    load_masters()

    ui.separator().classes("my-4")

    # --------------------
    # Actions
    # --------------------

    with ui.row().classes("gap-3 px-6"):

        def get_selected() -> dict | None:
            if not table.selected:
                ui.notify("Select a master first", color="warning")
                return None
            return table.selected[0]

        def view_master() -> None:
            row = get_selected()
            if not row:
                return
            with ui.dialog() as view_dialog, ui.card().classes("p-4 gap-1 w-96"):
                ui.label(row["name"]).classes("text-lg font-bold")
                ui.label(f"Specialization: {row['specialization']}")
                ui.label(f"City: {row['city']}")
                ui.label(f"Rating: {row['rating']}")
                ui.label(f"Bookings: {row['bookings']}")
                ui.label(f"Revenue: {row['revenue']}")
                ui.label(f"Type: {row['is_solo']}")
                ui.button("Close", on_click=view_dialog.close).classes("mt-2")
            view_dialog.open()

        ui.button("View", icon="visibility", on_click=view_master)
        ui.button("Edit", icon="edit")
        ui.button("Documents", icon="description")
        ui.button("Block", icon="block").props("color=red")