from nicegui import ui

from pages.layout import add_navigation


AI_FEATURES = [
    {
        "name": "Auto-reply to client messages",
        "description": "AI answers common client questions automatically",
        "enabled": True,
    },
    {
        "name": "Service recommendations",
        "description": "Suggest add-on services based on booking history",
        "enabled": True,
    },
    {
        "name": "No-show prediction",
        "description": "Flag bookings with high risk of no-show",
        "enabled": False,
    },
    {
        "name": "Smart scheduling",
        "description": "Auto-suggest optimal time slots for new bookings",
        "enabled": True,
    },
]


@ui.page("/ai")
def ai_page() -> None:

    add_navigation(active="/ai")

    ui.query("body").style("background:#F5F6FA")

    ui.label("AI").classes("text-3xl font-bold m-6")

    # =====================================================
    # Features
    # =====================================================

    ui.label("Features").classes(
        "text-xl font-bold px-6 mb-2"
    )

    @ui.refreshable
    def active_features_card() -> None:
        active_features = sum(
            1 for feature in AI_FEATURES
            if feature["enabled"]
        )

        ui.label("Active Features").classes(
            "text-sm text-gray-500"
        )

        ui.label(
            f"{active_features}/{len(AI_FEATURES)}"
        ).classes("text-2xl font-bold")

    with ui.column().classes(
        "px-6 gap-2 w-full"
    ):

        for feature in AI_FEATURES:

            def toggle_feature(
                value: bool,
                feature=feature,
            ) -> None:

                feature["enabled"] = value
                active_features_card.refresh()

            with ui.card().classes(
                "p-4 w-full"
            ):

                with ui.row().classes(
                    "items-center justify-between w-full"
                ):

                    with ui.column().classes("gap-0"):

                        ui.label(
                            feature["name"]
                        ).classes("font-semibold")

                        ui.label(
                            feature["description"]
                        ).classes(
                            "text-sm text-gray-500"
                        )

                    ui.switch(
                        value=feature["enabled"],
                        on_change=lambda e, f=feature:
                            toggle_feature(e.value, f),
                    )

    ui.separator().classes("my-4")

    # =====================================================
    # AI statistics
    # =====================================================
    #
    # Backend endpoint for AI search history/statistics
    # is not available yet.
    #
    # IMPORTANT:
    # Do not use local SQLite here.
    # When backend API is ready, replace these values
    # with data returned by the API.
    # =====================================================

    total_searches = 0
    accepted = 0

    acceptance_rate = (
        f"{accepted}/{total_searches}"
        if total_searches
        else "0/0"
    )

    with ui.row().classes(
        "px-6 gap-4 flex-wrap"
    ):

        with ui.card().classes("p-4 w-64"):

            ui.label(
                "Total AI Searches"
            ).classes(
                "text-sm text-gray-500"
            )

            ui.label(
                str(total_searches)
            ).classes(
                "text-2xl font-bold"
            )

        with ui.card().classes("p-4 w-64"):

            ui.label(
                "Recommendations Accepted"
            ).classes(
                "text-sm text-gray-500"
            )

            ui.label(
                acceptance_rate
            ).classes(
                "text-2xl font-bold"
            )

        with ui.card().classes("p-4 w-64"):
            active_features_card()

    ui.separator().classes("my-4")

    # =====================================================
    # Recent AI Activity
    # =====================================================

    ui.label(
        "Recent AI Activity"
    ).classes(
        "text-xl font-bold px-6 mb-2"
    )

    with ui.row().classes(
        "w-full px-6 gap-4 items-center mb-2"
    ):

        search_input = ui.input(
            placeholder="Search query or client..."
        ).props(
            "outlined dense"
        ).classes(
            "w-80"
        )

        type_filter = ui.select(
            ["All", "ai_search"],
            value="All",
            label="Type",
        ).classes(
            "w-48"
        )

    columns = [
        {
            "name": "id",
            "label": "ID",
            "field": "id",
            "align": "left",
        },
        {
            "name": "type",
            "label": "Type",
            "field": "type",
        },
        {
            "name": "client",
            "label": "Client",
            "field": "client",
        },
        {
            "name": "query",
            "label": "Query",
            "field": "query",
        },
        {
            "name": "recommended_service",
            "label": "Recommended",
            "field": "recommended_service",
        },
        {
            "name": "date",
            "label": "Date",
            "field": "date",
        },
        {
            "name": "status",
            "label": "Status",
            "field": "status",
        },
    ]

    table = ui.table(
        columns=columns,
        rows=[],
        row_key="id",
        pagination=10,
    ).classes(
        "w-full px-6"
    )

    # =====================================================
    # Activity loader
    # =====================================================

    def load_activity() -> None:
        """
        AI activity API endpoint is not available yet.

        Keep the table empty instead of reading
        from the local SQLite database.

        When backend endpoint is available,
        connect it here using api_get().
        """

        table.rows = []
        table.update()

        print(
            "[AI] Backend AI activity endpoint "
            "is not connected yet"
        )

    search_input.on(
        "keydown.enter",
        load_activity,
    )

    type_filter.on_value_change(
        load_activity
    )

    load_activity()