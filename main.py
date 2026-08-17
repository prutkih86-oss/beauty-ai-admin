from nicegui import ui

ui.add_head_html("""
<style>

.q-table,
.q-table__container {
    border: none !important;
    box-shadow: none !important;
}

.q-table thead tr th {
    background: #fafafa;
    border-bottom: 1px solid #e5e7eb;
    font-weight: 600;
}

.q-table tbody tr:hover {
    background: #f8fafc;
}

.q-table tbody tr:last-child td {
    border-bottom: none;
}
.q-table thead tr th{
    background:#fafafa;
    border-bottom:1px solid #e5e7eb;
    font-weight:600;
}

.q-table tbody tr:hover{
    background:#f8fafc;
    transition:.15s;
}

.q-table tbody tr td{
    border-bottom:1px solid #f1f5f9;
}

.q-table tbody tr:last-child td{
    border-bottom:none;
}
.q-table table {
    table-layout: auto !important;
    width: 100% !important;
}
.q-table__middle{
    overflow-x:hidden!important;
}
.q-table th,
.q-table td {
    white-space: nowrap;
}

</style>.q-table__middle{overflow-x:hidden!important;}
.q-table__container{overflow-x:hidden!important;}
.q-table{min-width:100%!important;}

""", shared=True)

from pages import (
    masters,
    clients,
    bookings,
    dashboard,
    services,
    payments,
    reviews,
    analytics,
    ai,
    settings,
)


@ui.page("/")
def index() -> None:
    ui.navigate.to("/dashboard")


ui.run(title="Beauty AI Admin", port=8080)