from nicegui import ui
import httpx

from pages.layout import add_navigation
from data_access.masters import get_masters


API_URL = os.environ.get(
    "API_BASE_URL", "https://beautyaiservice.polandcentral.cloudapp.azure.com"
)


@ui.page("users/masters")
def masters_page():

    add_navigation(active="/masters")

    ui.query("body").style("background:#F5F6FA")

    ui.label("Masters").classes("text-3xl font-bold m-6")

    # --------------------
    # API
    # --------------------

    def create_master(
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        bio: str,
        years_of_experience: int,
        photo: str,
    ) -> bool:

        payload = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "bio": bio,
            "years_of_experience": years_of_experience,
            "photo": photo,
        }

        try:
            response = httpx.put(
                f"{API_URL}/api/users/masters/me",
                json=payload,
                timeout=10,
            )

            if response.is_success:
                ui.notify(
                    "Master profile saved successfully",
                    color="positive",
                )
                return True

            print("Backend response:", response.text)

            ui.notify(
                f"Failed to save master: {response.status_code}",
                color="negative",
            )
            return False

        except httpx.RequestError as e:
            print("API error:", e)

            ui.notify(
                f"Cannot connect to backend: {e}",
                color="negative",
            )
            return False

    # --------------------
    # Toolbar
    # --------------------

    with ui.row().classes("w-full px-6 gap-4 items-center"):

        search_input = ui.input(
            placeholder="Search master..."
        ).props("outlined dense").classes("w-80")

        category_filter = ui.select(
            [
                "All",
                "Hair",
                "Barber",
                "Makeup",
                "Nails",
                "Brows",
                "Lashes",
                "Cosmetology",
                "Laser",
                "SPA",
                "Skincare",
            ],
            value="All",
            label="Specialization",
        ).classes("w-56")

        # --------------------
        # Add Master Dialog
        # --------------------

        with ui.dialog() as dialog, ui.card().classes("p-4 gap-2 w-96"):

            ui.label("Add Master").classes("text-lg font-bold")

            first_name_input = ui.input(
                label="First name"
            ).classes("w-full")

            last_name_input = ui.input(
                label="Last name"
            ).classes("w-full")

            email_input = ui.input(
                label="Email"
            ).classes("w-full")

            phone_input = ui.input(
                label="Phone"
            ).classes("w-full")

            bio_input = ui.textarea(
                label="Bio"
            ).classes("w-full")

            experience_input = ui.number(
                label="Years of experience",
                min=0,
                max=100,
                value=0,
            ).classes("w-full")

            photo_input = ui.input(
                label="Photo URL"
            ).classes("w-full")

            async def submit_master():

                first_name = (first_name_input.value or "").strip()
                last_name = (last_name_input.value or "").strip()
                email = (email_input.value or "").strip()
                phone = (phone_input.value or "").strip()
                bio = (bio_input.value or "").strip()
                photo = (photo_input.value or "").strip()

                if not first_name:
                    ui.notify(
                        "Enter first name",
                        color="negative",
                    )
                    return

                if not last_name:
                    ui.notify(
                        "Enter last name",
                        color="negative",
                    )
                    return

                if not email:
                    ui.notify(
                        "Enter email",
                        color="negative",
                    )
                    return

                years_of_experience = int(
                    experience_input.value or 0
                )

                payload = {
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "phone": phone,
                    "bio": bio,
                    "years_of_experience": years_of_experience,
                    "photo": photo,
                }

                print("Sending payload:")
                print(payload)

                try:
                    response = await httpx.AsyncClient().put(
                        f"{API_URL}/api/users/masters/me",
                        json=payload,
                        timeout=10,
                    )

                    print("Status:", response.status_code)
                    print("Response:", response.text)

                    if response.is_success:

                        ui.notify(
                            "Master added successfully",
                            color="positive",
                        )

                        dialog.close()
                        load_masters()

                    else:

                        ui.notify(
                            f"Backend error: {response.status_code}",
                            color="negative",
                        )

                except httpx.RequestError as e:

                    print("Request error:", e)

                    ui.notify(
                        f"Cannot connect to backend: {e}",
                        color="negative",
                    )

            with ui.row().classes(
                "justify-end gap-2 mt-2 w-full"
            ):

                ui.button(
                    "Cancel",
                    on_click=dialog.close,
                ).props("flat")

                ui.button(
                    "Save",
                    on_click=submit_master,
                ).classes("bg-purple-600 text-white")

        ui.space()

        ui.button(
            "Add Master",
            icon="add",
            on_click=dialog.open,
        ).classes("bg-purple-600 text-white")

    ui.separator().classes("my-4")

    # --------------------
    # Table
    # --------------------

    columns = [
        {
            "name": "name",
            "label": "Name",
            "field": "name",
            "align": "left",
        },
        {
            "name": "specialization",
            "label": "Specialization",
            "field": "specialization",
        },
        {
            "name": "rating",
            "label": "Rating",
            "field": "rating",
        },
        {
            "name": "city",
            "label": "City",
            "field": "city",
        },
        {
            "name": "bookings",
            "label": "Bookings",
            "field": "bookings",
        },
        {
            "name": "revenue",
            "label": "Revenue",
            "field": "revenue",
        },
        {
            "name": "is_solo",
            "label": "Solo",
            "field": "is_solo",
        },
    ]

    table = ui.table(
        columns=columns,
        rows=[],
        row_key="name",
        pagination=10,
        selection="single",
    ).classes("w-full px-6")

    def load_masters() -> None:

        rows = get_masters(
            search_input.value,
            category_filter.value,
        )

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

    search_input.on(
        "keydown.enter",
        load_masters,
    )

    category_filter.on_value_change(
        load_masters
    )

    load_masters()

    ui.separator().classes("my-4")

    # --------------------
    # Actions
    # --------------------

    with ui.row().classes("gap-3 px-6"):

        def get_selected() -> dict | None:

            if not table.selected:
                ui.notify(
                    "Select a master first",
                    color="warning",
                )
                return None

            return table.selected[0]

        def view_master() -> None:

            row = get_selected()

            if not row:
                return

            with ui.dialog() as view_dialog, ui.card().classes(
                "p-4 gap-1 w-96"
            ):

                ui.label(
                    row["name"]
                ).classes("text-lg font-bold")

                ui.label(
                    f"Specialization: {row['specialization']}"
                )

                ui.label(
                    f"City: {row['city']}"
                )

                ui.label(
                    f"Rating: {row['rating']}"
                )

                ui.label(
                    f"Bookings: {row['bookings']}"
                )

                ui.label(
                    f"Revenue: {row['revenue']}"
                )

                ui.label(
                    f"Type: {row['is_solo']}"
                )

                ui.button(
                    "Close",
                    on_click=view_dialog.close,
                ).classes("mt-2")

            view_dialog.open()

        ui.button(
            "View",
            icon="visibility",
            on_click=view_master,
        )

        ui.button(
            "Edit",
            icon="edit",
        )

        ui.button(
            "Documents",
            icon="description",
        )

        ui.button(
            "Block",
            icon="block",
        ).props("color=red")