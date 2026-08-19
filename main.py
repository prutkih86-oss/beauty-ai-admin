from nicegui import ui

# CSS стилі для приведення Quasar Table до мінімалістичного дизайну
ui.add_head_html(
    """
<style>
/* Скидання рамок та тіней контейнера */
.q-table,
.q-table__container {
    border: none !important;
    box-shadow: none !important;
}

/* Стилізація заголовків таблиці */
.q-table thead tr th {
    background: #fafafa;
    border-bottom: 1px solid #e5e7eb;
    font-weight: 600;
}

/* Оформлення рядків та ховер-ефект */
.q-table tbody tr {
    transition: background-color 0.15s ease;
}

.q-table tbody tr:hover {
    background: #f8fafc;
}

.q-table tbody tr td {
    border-bottom: 1px solid #f1f5f9;
    white-space: nowrap;
}

.q-table tbody tr:last-child td {
    border-bottom: none;
}

/* Налаштування ширини та поведінки скролу */
.q-table table {
    table-layout: auto !important;
    width: 100% !important;
}

.q-table {
    min-width: 100% !important;
}

.q-table__container,
.q-table__middle {
    overflow-x: auto !important; /* Авто-скрол замість hidden, щоб таблиці не обрізалися на малих екранах */
}
</style>
""",
    shared=True,
)

from pages import (
    ai,
    analytics,
    bookings,
    clients,
    dashboard,
    masters,
    salons,
    payments,
    reviews,
    services,
    settings,
)


@ui.page("/")
def index() -> None:
    ui.navigate.to("/dashboard")


ui.run(title="Beauty AI Admin", port=8080)