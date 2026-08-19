from nicegui import ui

from pages.layout import add_navigation
from data_access.services import get_services


@ui.page("/services")
def services_page() -> None:

    add_navigation(active="/services")

    ui.query("body").style("background:#F5F6FA")

    ui.label("Services").classes("text-3xl font-bold m-6")

    with ui.row().classes("w-full px-6 gap-4 items-center"):

        search_input = (
            ui.input(placeholder="Search service...")
            .props("outlined dense")
            .classes("w-80")
        )

        category_filter = ui.select(
            [
                "All",
                "Barber",
                "Brows",
                "Cosmetology",
                "Hair",
                "Laser",
                "Lashes",
                "Makeup",
                "Nails",
                "SPA",
                "Skincare",
            ],
            value="All",
            label="Category",
        ).classes("w-56")

        ui.space()

        ui.button(
            "Add Service",
            icon="add",
            on_click=lambda: ui.notify(
                "Adding services via API is not connected yet",
                color="warning",
            ),
        ).classes("bg-purple-600 text-white")

    ui.separator().classes("my-4")

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
        row_key="id",
        pagination=10,
        selection="single",
    ).classes("w-full px-6")

    def load_services() -> None:

        try:
            services = get_services(
                search=search_input.value or "",
                category=category_filter.value or "All",
            )
        except Exception as e:
            print(f"[Services Page Error]: {e}")
            ui.notify(
                f"Could not load services: {e}",
                color="negative",
            )
            table.rows = []
            table.update()
            return

        table.rows = [
            {
                "id": service.id,
                "name": service.name,
                "category": service.category,
                "duration": f"{service.duration} min",
                "price": f"${service.price:,.0f}",
                "masters": service.masters,
                "bookings": service.bookings,
            }
            for service in services
        ]

        table.selected.clear()
        table.update()

        print(f"[Services API] Loaded {len(table.rows)} services")

    search_input.on("keydown.enter", load_services)
    category_filter.on_value_change(load_services)

    load_services()

    ui.separator().classes("my-4")

    def get_selected() -> dict | None:
        if not table.selected:
            ui.notify("Select a service first", color="warning")
            return None

        return table.selected[0]

    def view_service() -> None:
        row = get_selected()

        if not row:
            return

        with ui.dialog() as dialog, ui.card().classes("p-4 gap-1 w-96"):
            ui.label(row["name"]).classes("text-lg font-bold")
            ui.label(f"Category: {row['category']}")
            ui.label(f"Duration: {row['duration']}")
            ui.label(f"Price: {row['price']}")
            ui.label(f"Master(s): {row['masters']}")
            ui.label(f"Bookings: {row['bookings']}")

            ui.button(
                "Close",
                on_click=dialog.close,
            ).classes("mt-2")

        dialog.open()

    def edit_service() -> None:
        if not get_selected():
            return

        ui.notify(
            "Editing services via API is not connected yet",
            color="warning",
        )

    def deactivate_service() -> None:
        if not get_selected():
            return

        ui.notify(
            "Deactivating services via API is not connected yet",
            color="warning",
        )

    def delete_service() -> None:
        if not get_selected():
            return

        ui.notify(
            "Deleting services via API is not connected yet",
            color="warning",
        )

    with ui.row().classes("gap-3 px-6"):

        ui.button(
            "View",
            icon="visibility",
            on_click=view_service,
        )

        ui.button(
            "Edit",
            icon="edit",
            on_click=edit_service,
        )

        ui.button(
            "Deactivate",
            icon="block",
            on_click=deactivate_service,
        ).props("color=orange")

        ui.button(
            "Delete",
            icon="delete",
            on_click=delete_service,
        ).props("color=red")