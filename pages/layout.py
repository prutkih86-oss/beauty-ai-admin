from nicegui import ui

NAV_ITEMS = [
    ("Dashboard", "/dashboard", "dashboard"),
    ("Analytics", "/analytics", "insights"),

    None,  # ← розділювач

    ("Masters", "/masters", "badge"),
    ("Clients", "/clients", "groups"),
    ("Bookings", "/bookings", "event"),
    ("Services", "/services", "content_cut"),
    ("Payments", "/payments", "payments"),
    ("Reviews", "/reviews", "star"),

    None,  # ← ще один розділювач

    ("AI", "/ai", "auto_awesome"),
    ("Settings", "/settings", "settings"),
]

def add_navigation(active: str) -> None:

    with ui.header().classes(
        "bg-white text-black shadow-sm items-center px-4"
    ):
        ui.button(icon="menu", on_click=lambda: drawer.toggle()).props(
            "flat dense"
        )
        ui.label("Beauty AI Admin").classes("text-xl font-bold ml-2")

    with ui.left_drawer(value=True).classes("bg-white") as drawer:

        for item in NAV_ITEMS:

            if item is None:
                ui.separator().classes("my-2 mx-4")
                continue

            label, path, icon = item

            is_active = path == active

            with ui.link(target=path).classes("no-underline w-full"):
             with ui.row().classes(
            "items-center gap-3 px-4 py-2 rounded-md w-full "
            + (
                "bg-purple-100 text-purple-700 font-semibold"
                if is_active
                else "text-gray-700 hover:bg-gray-100"
                 )
             ):
                    ui.icon(icon)
                    ui.label(label)