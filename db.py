import sqlite3
import json
from pathlib import Path
from datetime import datetime


# ============================
# DATABASE FILE PATH
# ============================
DB_PATH = Path("fake_shop.db")


# ============================
# CONNECT FUNCTION
# ============================
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============================
# INITIALIZE DATABASE
# ============================
def init_db():
    conn = get_conn()
    c = conn.cursor()

    # USERS TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY,
        name TEXT,
        age INTEGER,
        password_hash TEXT,
        created_at TEXT
    );
    """)

    # ORDERS TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        invoice_id TEXT PRIMARY KEY,
        created_at TEXT,
        customer_email TEXT,
        items_json TEXT,
        category TEXT,
        total REAL,
        status TEXT
    );
    """)

     # ⭐ LOGIN LOGS TABLE ⭐
    c.execute("""
    CREATE TABLE IF NOT EXISTS login_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        login_time TEXT
    );
    """)

    conn.commit()
    conn.close()
    
    
   

# ============================
# LOAD PRODUCTS FROM JSON
# ============================
def load_products_from_json(json_path="products/products.json"):
    p = Path(json_path)
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


# ============================
# SAVE USER
# ============================
def save_user(email, name, age, password_hash):
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        INSERT INTO users (email, name, age, password_hash, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        email, name, age, password_hash,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


# ============================
# LOGIN CHECK
# ============================
def get_user(email, password_hash):
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        SELECT * FROM users 
        WHERE email = ? AND password_hash = ?
    """, (email, password_hash))

    user = c.fetchone()
    conn.close()
    return user


# ============================
# SAVE ORDER
# ============================
def save_order(invoice_id, customer_email, items, total, status="PLACED"):
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        INSERT INTO orders 
        (invoice_id, created_at, customer_email, items_json, total, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        invoice_id,
        datetime.now().isoformat(),
        customer_email,
        json.dumps(items),
        total,
        status
    ))

    conn.commit()
    conn.close()


# ============================
# GET ORDERS AS DATAFRAME
# ============================
def get_orders_df():
    import pandas as pd
    conn = get_conn()

    df = pd.read_sql_query("SELECT * FROM orders", conn)

    if not df.empty:
        df["created_at"] = pd.to_datetime(df["created_at"])
        df["items_parsed"] = df["items_json"].apply(json.loads)

    conn.close()
    return df
