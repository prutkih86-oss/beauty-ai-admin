from nicegui import ui

from pages.layout import add_navigation
from data_access.salons import get_salons


@ui.page("/salons")
def salons_page() -> None:

    add_navigation(active="/salons")

    ui.query("body").style("background:#F5F6FA")

    ui.label("Salons").classes("text-3xl font-bold m-6")

    # -----------------------------
    # Toolbar
    # -----------------------------

    with ui.row().classes("w-full px-6 gap-4 items-center"):

        search_input = (
            ui.input(placeholder="Search salon...")
            .props("outlined dense")
            .classes("w-80")
        )

        ui.space()

        ui.button(
            "Add Salon",
            icon="add_business",
            on_click=lambda: ui.notify(
                "Adding salons via API is not connected yet",
                color="warning",
            ),
        ).classes("bg-purple-600 text-white")

    ui.separator().classes("my-4")

    # -----------------------------
    # Table
    # -----------------------------

    columns = [
        {"name": "id", "label": "ID", "field": "id", "align": "left"},
        {"name": "name", "label": "Salon", "field": "name"},
        {"name": "city", "label": "City", "field": "city"},
        {"name": "address", "label": "Address", "field": "address"},
        {
            "name": "popularity",
            "label": "Popularity",
            "field": "popularity",
        },
    ]

    table = ui.table(
        columns=columns,
        rows=[],
        row_key="id",
        pagination=10,
        selection="single",
    ).classes("w-full px-6")

    # -----------------------------
    # Load salons
    # -----------------------------

    def load_salons() -> None:

        try:
            salons = get_salons(
                search=search_input.value or ""
            )
        except Exception as e:
            print(f"[Salons Page Error]: {e}")
            ui.notify(
                f"Could not load salons: {e}",
                color="negative",
            )
            table.rows = []
            table.update()
            return

        table.rows = [
            {
                "id": salon.id,
                "name": salon.name,
                "city": salon.city,
                "address": salon.address or "—",
                "popularity": salon.popularity_score,
            }
            for salon in salons
        ]

        table.selected.clear()
        table.update()

        print(f"[Salons API] Loaded {len(table.rows)} salons")

    search_input.on("keydown.enter", load_salons)

    load_salons()

    ui.separator().classes("my-4")

    # -----------------------------
    # Selection helper
    # -----------------------------

    def get_selected() -> dict | None:

        if not table.selected:
            ui.notify(
                "Select a salon first",
                color="warning",
            )
            return None

        return table.selected[0]

    # -----------------------------
    # View
    # -----------------------------

    def view_salon() -> None:

        row = get_selected()

        if not row:
            return

        with ui.dialog() as dialog, ui.card().classes(
            "p-4 gap-1 w-96"
        ):

            ui.label(row["name"]).classes(
                "text-lg font-bold"
            )

            ui.label(f"ID: {row['id']}")
            ui.label(f"City: {row['city']}")
            ui.label(f"Address: {row['address']}")
            ui.label(
                f"Popularity: {row['popularity']}"
            )

            ui.button(
                "Close",
                on_click=dialog.close,
            ).classes("mt-2")

        dialog.open()

    # -----------------------------
    # API actions not connected yet
    # -----------------------------

    def edit_salon() -> None:

        if not get_selected():
            return

        ui.notify(
            "Editing salons via API is not connected yet",
            color="warning",
        )

    def delete_salon() -> None:

        if not get_selected():
            return

        ui.notify(
            "Deleting salons via API is not connected yet",
            color="warning",
        )

    # -----------------------------
    # Action bar
    # -----------------------------

    with ui.row().classes("gap-3 px-6"):

        ui.button(
            "View",
            icon="visibility",
            on_click=view_salon,
        )

        ui.button(
            "Edit",
            icon="edit",
            on_click=edit_salon,
        )

        ui.button(
            "Delete",
            icon="delete",
            on_click=delete_salon,
        ).props("color=red")