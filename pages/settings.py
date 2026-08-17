from nicegui import ui
from pages.layout import add_navigation
from data_access.salons import get_salons, add_salon, update_salon, delete_salon
from data_access.settings import get_all_settings, save_settings_batch


NOTIFICATIONS = [
    {"id": "notif_new_booking", "name": "New booking created", "email": True, "sms": False},
    {"id": "notif_cancelled", "name": "Booking cancelled", "email": True, "sms": True},
    {"id": "notif_payment", "name": "Payment received", "email": True, "sms": False},
    {"id": "notif_review", "name": "New review submitted", "email": False, "sms": False},
    {"id": "notif_noshow", "name": "No-show flagged by AI", "email": True, "sms": True},
]


@ui.page("/settings")
def settings_page() -> None:

    add_navigation(active="/settings")

    ui.query("body").style("background:#F5F6FA")

    app_settings = get_all_settings()

    ui.label("Settings").classes("text-3xl font-bold m-6")

    ui.label("Business Profile").classes("text-xl font-bold px-6 mb-2")

    with ui.card().classes("mx-6 p-4"):
        with ui.row().classes("gap-4 flex-wrap"):
            business_name_input = ui.input(
                label="Business name",
                value=app_settings.get("business_name", "Beauty AI Salon"),
            ).classes("w-64")
            
            support_email_input = ui.input(
                label="Support email",
                value=app_settings.get("support_email", "support@beautyai.com"),
            ).classes("w-64")
            
            support_phone_input = ui.input(
                label="Support phone",
                value=app_settings.get("support_phone", "+380441112233"),
            ).classes("w-64")

        with ui.row().classes("gap-4 flex-wrap mt-2"):
            currency_select = ui.select(
                ["USD", "EUR", "UAH"],
                value=app_settings.get("currency", "USD"),
                label="Currency",
            ).classes("w-40")
            
            timezone_select = ui.select(
                ["Europe/Kyiv", "Europe/Warsaw", "UTC"],
                value=app_settings.get("timezone", "Europe/Kyiv"),
                label="Timezone",
            ).classes("w-48")

    ui.separator().classes("my-4")

    # branches section
    def add_branch_submit(salon_name: str, city: str, address: str) -> None:
        if not salon_name.strip():
            ui.notify("Enter salon name", color="negative")
            return

        add_salon(salon_name, city, address)
        ui.notify(f"Branch '{salon_name}' added", color="positive")
        add_branch_dialog.close()
        load_branches()

    with ui.dialog() as add_branch_dialog, ui.card().classes("p-4 gap-2 w-96"):
        ui.label("Add Branch").classes("text-lg font-bold")

        branch_name_input = ui.input(label="Salon name").classes("w-full")
        branch_city_input = ui.input(label="City").classes("w-full")
        branch_address_input = ui.input(label="Address").classes("w-full")

        with ui.row().classes("justify-end gap-2 mt-2 w-full"):
            ui.button("Cancel", on_click=add_branch_dialog.close).props("flat")
            ui.button(
                "Save",
                on_click=lambda: add_branch_submit(
                    branch_name_input.value or "",
                    branch_city_input.value or "",
                    branch_address_input.value or "",
                ),
            ).classes("bg-purple-600 text-white")

    with ui.row().classes("w-full px-6 items-center justify-between"):
        ui.label("Branches").classes("text-xl font-bold")
        ui.button("Add Branch", icon="add", on_click=add_branch_dialog.open).classes(
            "bg-purple-600 text-white"
        )

    with ui.row().classes("w-full px-6 gap-4 items-center mt-2"):
        search_input = (
            ui.input(placeholder="Search branch...")
            .props("outlined dense")
            .classes("w-80")
        )

    branch_columns = [
        {"name": "id", "label": "ID", "field": "id", "align": "left"},
        {"name": "salon_name", "label": "Salon", "field": "salon_name", "align": "left"},
        {"name": "city", "label": "City", "field": "city"},
        {"name": "address", "label": "Address", "field": "address"},
        {"name": "popularity_score", "label": "Rating", "field": "popularity_score"},
    ]

    branch_table = ui.table(
        columns=branch_columns,
        rows=[],
        row_key="id",
        pagination=10,
        selection="single",
    ).classes("w-full px-6 mt-2")

    def load_branches() -> None:
        rows = get_salons(search_input.value)
        branch_table.rows = [
            {
                "id": r.id,
                "salon_name": r.name,
                "city": r.city,
                "address": r.address,
                "popularity_score": r.popularity_score,
            }
            for r in rows
        ]
        branch_table.update()

    search_input.on("keydown.enter", load_branches)
    load_branches()

    with ui.row().classes("gap-3 px-6 mt-2"):

        def get_selected_branch() -> dict | None:
            if not branch_table.selected:
                ui.notify("Select a branch first", color="warning")
                return None
            return branch_table.selected[0]

        def edit_branch() -> None:
            row = get_selected_branch()
            if not row:
                return

            def save_edit(new_city: str, new_address: str) -> None:
                update_salon(row["id"], new_city, new_address)
                ui.notify(f"Updated {row['salon_name']}", color="positive")
                edit_branch_dialog.close()
                load_branches()

            with ui.dialog() as edit_branch_dialog, ui.card().classes("p-4 gap-2 w-96"):
                ui.label(f"Edit {row['salon_name']}").classes("text-lg font-bold")

                city_edit = ui.input(label="City", value=row["city"]).classes("w-full")
                address_edit = ui.input(label="Address", value=row["address"]).classes("w-full")

                with ui.row().classes("justify-end gap-2 mt-2 w-full"):
                    ui.button("Cancel", on_click=edit_branch_dialog.close).props("flat")
                    ui.button(
                        "Save",
                        on_click=lambda: save_edit(city_edit.value or "", address_edit.value or ""),
                    ).classes("bg-purple-600 text-white")

            edit_branch_dialog.open()

        def delete_branch() -> None:
            row = get_selected_branch()
            if not row:
                return

            def confirm_delete() -> None:
                try:
                    delete_salon(row["id"])
                    ui.notify(f"'{row['salon_name']}' deleted", color="positive")
                    load_branches()
                except Exception as e:
                    ui.notify(f"Could not delete: {e}", color="negative")
                delete_branch_dialog.close()

            with ui.dialog() as delete_branch_dialog, ui.card().classes("p-4 gap-2 w-80"):
                ui.label(f"Delete '{row['salon_name']}'?").classes("text-lg font-bold")
                ui.label(
                    "Masters assigned to this salon may reference it — "
                    "deleting may fail if the database enforces foreign keys."
                ).classes("text-sm text-gray-500")
                with ui.row().classes("justify-end gap-2 mt-2 w-full"):
                    ui.button("Cancel", on_click=delete_branch_dialog.close).props("flat")
                    ui.button("Delete", on_click=confirm_delete).props("color=red")

            delete_branch_dialog.open()

        ui.button("Edit", icon="edit", on_click=edit_branch)
        ui.button("Delete", icon="delete", on_click=delete_branch).props("color=red")

    ui.separator().classes("my-4")

    # notifications
    ui.label("Notifications").classes("text-xl font-bold px-6 mb-2")

    notif_switches = {}

    with ui.column().classes("px-6 gap-2 w-full"):
        for notif in NOTIFICATIONS:
            with ui.card().classes("p-4 w-full"):
                with ui.row().classes("items-center justify-between w-full"):
                    ui.label(notif["name"]).classes("font-medium")

                    with ui.row().classes("gap-6 items-center"):
                        with ui.row().classes("items-center gap-1"):
                            ui.label("Email").classes("text-sm text-gray-500")
                            sw_email = ui.switch(value=notif["email"])

                        with ui.row().classes("items-center gap-1"):
                            ui.label("SMS").classes("text-sm text-gray-500")
                            sw_sms = ui.switch(value=notif["sms"])

                        notif_switches[notif["id"]] = {"email": sw_email, "sms": sw_sms}

    ui.separator().classes("my-4")

    # security
    ui.label("Account & Security").classes("text-xl font-bold px-6 mb-2")

    with ui.card().classes("mx-6 p-4"):
        with ui.row().classes("gap-4 flex-wrap items-center"):
            admin_email_input = ui.input(
                label="Admin email",
                value=app_settings.get("admin_email", "admin@beautyai.com"),
            ).classes("w-64")
            
            ui.button("Change Password", icon="lock")
            tfa_switch = ui.switch(
                "Two-factor authentication",
                value=app_settings.get("tfa_enabled", "False") == "True",
            )

    ui.separator().classes("my-4")

    def save_all_settings() -> None:
        data_to_save = {
            "business_name": business_name_input.value or "",
            "support_email": support_email_input.value or "",
            "support_phone": support_phone_input.value or "",
            "currency": currency_select.value,
            "timezone": timezone_select.value,
            "admin_email": admin_email_input.value or "",
            "tfa_enabled": str(tfa_switch.value),
        }

        save_settings_batch(data_to_save)
        ui.notify("Settings saved successfully", color="positive")

    with ui.row().classes("px-6 pb-6"):
        ui.button("Save Changes", icon="save", on_click=save_all_settings).classes(
            "bg-purple-600 text-white"
        )