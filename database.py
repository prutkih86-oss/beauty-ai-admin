import sqlite3

DB_PATH = r"C:\Users\IGOR\Desktop\powr bi dashboard\beauty_line_db-v12-gender.sqlite3"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn