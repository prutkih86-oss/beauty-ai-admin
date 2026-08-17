from nicegui import ui
from pages.layout import add_navigation
from database import get_connection
from data_access.reviews import get_reviews

@ui.page("/reviews")
def reviews_page() -> None:

    add_navigation(active="/reviews")

    ui.query("body").style("background:#F5F6FA")

    ui.label("Reviews").classes("text-3xl font-bold m-6")

    # --------------------
    # Toolbar
    # --------------------

    with ui.row().classes("w-full px-6 gap-4 items-center"):

        search_input = ui.input(
            placeholder="Search review..."
        ).props("outlined dense").classes("w-80")

        rating_filter = ui.select(
            ["All", "5", "4", "3", "2", "1"],
            value="All",
            label="Rating",
        ).classes("w-36")

        ui.space()

    ui.separator().classes("my-4")

    # --------------------
    # Table
    # --------------------

    columns = [
        {"name": "id", "label": "ID", "field": "id", "align": "left"},
        {"name": "client", "label": "Client", "field": "client"},
        {"name": "master", "label": "Master", "field": "master"},
        {"name": "service", "label": "Service", "field": "service"},
        {"name": "rating", "label": "Rating", "field": "rating"},
        {"name": "date", "label": "Date", "field": "date"},
    ]

    table = ui.table(
        columns=columns,
        rows=[],
        row_key="id",
        pagination=10,
        selection="single",
    ).classes("w-full px-6")

    def load_reviews() -> None:
        rows = get_reviews(search_input.value, rating_filter.value)

        table.rows = [
            {
                "id": r.id,
                "client": r.client,
                "master": r.master,
                "service": r.service,
                "rating": r.rating,
                "date": r.date,
            }
            for r in rows
        ]
        table.update()

    search_input.on("keydown.enter", load_reviews)
    rating_filter.on_value_change(load_reviews)

    load_reviews()

    ui.separator().classes("my-4")

    # --------------------
    # Actions
    # --------------------

    with ui.row().classes("gap-3 px-6"):

        def get_selected() -> dict | None:
            if not table.selected:
                ui.notify("Select a review first", color="warning")
                return None
            return table.selected[0]

        def view_review() -> None:
            row = get_selected()
            if not row:
                return
            with ui.dialog() as view_dialog, ui.card().classes("p-4 gap-1 w-96"):
                ui.label(f"Review #{row['id']}").classes("text-lg font-bold")
                ui.label(f"Client: {row['client']}")
                ui.label(f"Master: {row['master']}")
                ui.label(f"Service: {row['service']}")
                ui.label(f"Rating: {row['rating']} / 5")
                ui.label(f"Date: {row['date']}")
                ui.button("Close", on_click=view_dialog.close).classes("mt-2")
            view_dialog.open()

        def hide_review() -> None:
            row = get_selected()
            if not row:
                return
            ui.notify(
                f"No visibility/status column in reviews table yet for review #{row['id']}",
                color="info",
            )

        def delete_review() -> None:
            row = get_selected()
            if not row:
                return

            def confirm_delete() -> None:
                from data_access.reviews import delete_review as delete_review_data
                try:
                    delete_review_data(row["id"])
                    ui.notify(f"Review #{row['id']} deleted", color="positive")
                    load_reviews()
                except Exception as e:
                    ui.notify(f"Could not delete: {e}", color="negative")
                delete_dialog.close()

            with ui.dialog() as delete_dialog, ui.card().classes("p-4 gap-2 w-80"):
                ui.label(f"Delete review #{row['id']}?").classes("text-lg font-bold")
                ui.label(f"{row['client']} — {row['rating']}/5 for {row['service']}").classes(
                    "text-sm text-gray-500"
                )
                with ui.row().classes("justify-end gap-2 mt-2 w-full"):
                    ui.button("Cancel", on_click=delete_dialog.close).props("flat")
                    ui.button("Delete", on_click=confirm_delete).props("color=red")

            delete_dialog.open()

        ui.button("View", icon="visibility", on_click=view_review)
        ui.button("Hide", icon="visibility_off", on_click=hide_review).props("color=orange")
        ui.button("Delete", icon="delete", on_click=delete_review).props("color=red")