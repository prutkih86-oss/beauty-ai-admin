from nicegui import ui
from pages.layout import add_navigation
from database import get_connection
from data_access.payments import get_payments, add_payment as add_payment_data, delete_payment as delete_payment_data


@ui.page("/payments")
def payments_page() -> None:

    add_navigation(active="/payments")

    ui.query("body").style("background:#F5F6FA")

    ui.label("Payments").classes("text-3xl font-bold m-6")

    # --------------------
    # Toolbar
    # --------------------

    with ui.row().classes("w-full px-6 gap-4 items-center"):

        search_input = ui.input(
            placeholder="Search payment..."
        ).props("outlined dense").classes("w-80")

        method_filter = ui.select(
            ["All", "Card", "Cash", "Apple Pay", "Google Pay"],
            value="All",
            label="Method",
        ).classes("w-40")

        date_filter = ui.input(
            placeholder="Date"
        ).props("outlined dense type=date").classes("w-48")

        ui.space()

        def load_unpaid_bookings() -> dict:
            conn = get_connection()
            cursor = conn.cursor()
            rows = cursor.execute(
                """
                SELECT b.booking_id AS id, c.client_name AS client, s.service_name AS service,
                       b.booking_datetime AS booking_datetime
                FROM bookings b
                JOIN clients c ON c.client_id = b.client_id
                JOIN services s ON s.service_id = b.service_id
                LEFT JOIN payments p ON p.booking_id = b.booking_id
                WHERE p.payment_id IS NULL
                ORDER BY b.booking_datetime DESC
                LIMIT 100
                """
            ).fetchall()
            conn.close()
            return {
                f"#{r['id']} — {r['client']} — {r['service']} ({r['booking_datetime'][:16]})": r["id"]
                for r in rows
            }

        def add_payment(booking_label: str, amount: float, method: str) -> None:
            if not booking_label:
                ui.notify("Select a booking", color="negative")
                return
            if amount <= 0:
                ui.notify("Amount must be positive", color="negative")
                return

            booking_id = unpaid_bookings[booking_label]
            add_payment_data(booking_id, amount, method)

            ui.notify("Payment added", color="positive")
            add_dialog.close()
            load_payments()

        unpaid_bookings = load_unpaid_bookings()

        with ui.dialog() as add_dialog, ui.card().classes("p-4 gap-2 w-[420px]"):
            ui.label("Add Payment").classes("text-lg font-bold")

            if not unpaid_bookings:
                ui.label("No unpaid bookings found.").classes("text-sm text-gray-500")

            booking_select = ui.select(
                list(unpaid_bookings.keys()), label="Booking", with_input=True
            ).classes("w-full")
            amount_input = ui.number(label="Amount ($)", value=0, min=1, step=1).classes("w-full")
            method_input = ui.select(
                ["Card", "Cash", "Apple Pay", "Google Pay"], label="Method", value="Card"
            ).classes("w-full")

            with ui.row().classes("justify-end gap-2 mt-2 w-full"):
                ui.button("Cancel", on_click=add_dialog.close).props("flat")
                ui.button(
                    "Save",
                    on_click=lambda: add_payment(
                        booking_select.value, float(amount_input.value or 0), method_input.value
                    ),
                ).classes("bg-purple-600 text-white")

        ui.button("Add Payment", icon="add", on_click=add_dialog.open).classes(
            "bg-purple-600 text-white"
        )

    ui.separator().classes("my-4")

    # --------------------
    # Table
    # --------------------

    columns = [
        {"name": "id", "label": "ID", "field": "id", "align": "left"},
        {"name": "client", "label": "Client", "field": "client"},
        {"name": "booking_id", "label": "Booking", "field": "booking_id"},
        {"name": "amount", "label": "Amount", "field": "amount"},
        {"name": "method", "label": "Method", "field": "method"},
        {"name": "date", "label": "Date", "field": "date"},
    ]

    table = ui.table(
        columns=columns,
        rows=[],
        row_key="id",
        pagination=10,
        selection="single",
    ).classes("w-full px-6")

    def load_payments() -> None:
        rows = get_payments(search_input.value, method_filter.value, date_filter.value)

        table.rows = [
            {
                "id": r.id,
                "client": r.client,
                "booking_id": r.booking_id,
                "amount": f"${r.amount:,.0f}",
                "method": r.method,
                "date": r.date,
            }
            for r in rows
        ]
        table.update()

    search_input.on("keydown.enter", load_payments)
    method_filter.on_value_change(load_payments)
    date_filter.on_value_change(load_payments)

    load_payments()

    ui.separator().classes("my-4")

    # --------------------
    # Actions
    # --------------------

    with ui.row().classes("gap-3 px-6"):

        def get_selected() -> dict | None:
            if not table.selected:
                ui.notify("Select a payment first", color="warning")
                return None
            return table.selected[0]

        def view_payment() -> None:
            row = get_selected()
            if not row:
                return
            with ui.dialog() as view_dialog, ui.card().classes("p-4 gap-1 w-96"):
                ui.label(f"Payment #{row['id']}").classes("text-lg font-bold")
                ui.label(f"Client: {row['client']}")
                ui.label(f"Booking: #{row['booking_id']}")
                ui.label(f"Amount: {row['amount']}")
                ui.label(f"Method: {row['method']}")
                ui.label(f"Date: {row['date']}")
                ui.button("Close", on_click=view_dialog.close).classes("mt-2")
            view_dialog.open()

        def edit_payment() -> None:
            row = get_selected()
            if not row:
                return

            def save_edit(new_amount: float, new_method: str) -> None:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE payments SET amount = ?, payment_method = ? WHERE payment_id = ?",
                    (new_amount, new_method, row["id"]),
                )
                conn.commit()
                conn.close()
                ui.notify(f"Payment #{row['id']} updated", color="positive")
                edit_dialog.close()
                load_payments()

            with ui.dialog() as edit_dialog, ui.card().classes("p-4 gap-2 w-96"):
                ui.label(f"Edit Payment #{row['id']}").classes("text-lg font-bold")

                amount_edit = ui.number(
                    label="Amount ($)",
                    value=float(row["amount"].replace("$", "").replace(",", "")),
                    min=1,
                    step=1,
                ).classes("w-full")
                method_edit = ui.select(
                    ["Card", "Cash", "Apple Pay", "Google Pay"], label="Method", value=row["method"]
                ).classes("w-full")

                with ui.row().classes("justify-end gap-2 mt-2 w-full"):
                    ui.button("Cancel", on_click=edit_dialog.close).props("flat")
                    ui.button(
                        "Save",
                        on_click=lambda: save_edit(float(amount_edit.value or 0), method_edit.value),
                    ).classes("bg-purple-600 text-white")

            edit_dialog.open()

        def refund_payment() -> None:
            row = get_selected()
            if not row:
                return

            def confirm_refund() -> None:
                try:
                    delete_payment_data(row["id"])
                    ui.notify(f"Payment #{row['id']} refunded", color="positive")
                    load_payments()
                except Exception as e:
                    ui.notify(f"Could not refund: {e}", color="negative")
                refund_dialog.close()

            with ui.dialog() as refund_dialog, ui.card().classes("p-4 gap-2 w-80"):
                ui.label(f"Refund payment #{row['id']}?").classes("text-lg font-bold")
                ui.label(
                    f"{row['client']} · {row['amount']} · {row['method']}. "
                    "There is no separate 'refunded' status in the database — refunding removes the payment record."
                ).classes("text-sm text-gray-500")
                with ui.row().classes("justify-end gap-2 mt-2 w-full"):
                    ui.button("Back", on_click=refund_dialog.close).props("flat")
                    ui.button("Refund", on_click=confirm_refund).props("color=orange")

            refund_dialog.open()

        def delete_payment() -> None:
            row = get_selected()
            if not row:
                return

            def confirm_delete() -> None:
                try:
                    delete_payment_data(row["id"])
                    ui.notify(f"Payment #{row['id']} deleted", color="positive")
                    load_payments()
                except Exception as e:
                    ui.notify(f"Could not delete: {e}", color="negative")
                delete_dialog.close()

            with ui.dialog() as delete_dialog, ui.card().classes("p-4 gap-2 w-80"):
                ui.label(f"Delete payment #{row['id']}?").classes("text-lg font-bold")
                with ui.row().classes("justify-end gap-2 mt-2 w-full"):
                    ui.button("Cancel", on_click=delete_dialog.close).props("flat")
                    ui.button("Delete", on_click=confirm_delete).props("color=red")

            delete_dialog.open()

        ui.button("View", icon="visibility", on_click=view_payment)
        ui.button("Edit", icon="edit", on_click=edit_payment)
        ui.button("Refund", icon="undo", on_click=refund_payment).props("color=orange")
        ui.button("Delete", icon="delete", on_click=delete_payment).props("color=red")