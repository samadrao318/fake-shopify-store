import streamlit as st
import pandas as pd
from db import get_conn
import plotly.express as px
import json
from pathlib import Path
import shutil
import uuid

PRODUCTS_JSON = Path("products/products.json")
IMAGES_DIR = Path("products/images")

def admin_page():
    # SECURITY CHECK: sirf admin@gmail.com access kar sake
    admin = "samadrao318@gmail.com"
    if "user" not in st.session_state or st.session_state.user != admin :
        st.error("⛔ Access Denied! Admin Only.")
        return

    st.title("🛠️ Admin Dashboard")

    st.subheader("📊 Login Analytics")
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM login_logs", conn)
    conn.close()

    if not df.empty:
        df["login_time"] = pd.to_datetime(df["login_time"])
        df["date"] = df["login_time"].dt.date
        today = pd.Timestamp.today().date()
        today_count = df[df["date"] == today].shape[0]
        st.metric("Today's Logins", today_count)

        # DAILY LOGIN BAR
        daily_counts = df.groupby("date").size().reset_index(name="logins")
        fig = px.bar(
            daily_counts,
            x="date",
            y="logins",
            title="Daily Logins",
            labels={"logins": "Number of Logins", "date": "Date"},
            text="logins"
        )
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("📄 User Login History")
        st.dataframe(df)
    else:
        st.warning("No logins recorded yet.")

    st.markdown("---")
    st.subheader("➕ Add New Product")

    # --- Product Form ---
    with st.form("add_product_form"):
        title = st.text_input("Product Title")
        price = st.number_input("Price ($)", min_value=0.0, format="%.2f")
        category = st.text_input("Category")
        stock = st.number_input("Stock Quantity", min_value=0)
        image_file = st.file_uploader("Upload Product Image", type=["jpg", "jpeg", "png"])
        submit = st.form_submit_button("Add Product")

    # --- Handle Form Submission ---
    if submit:
        if not title or not category or not image_file:
            st.error("Please fill all fields and upload an image.")
        else:
            # --- Save image ---
            IMAGES_DIR.mkdir(parents=True, exist_ok=True)
            image_ext = Path(image_file.name).suffix
            unique_image_name = f"{uuid.uuid4().hex}{image_ext}"
            image_path = IMAGES_DIR / unique_image_name
            with open(image_path, "wb") as f:
                f.write(image_file.getbuffer())

            # --- Load existing JSON ---
            PRODUCTS_JSON.parent.mkdir(parents=True, exist_ok=True)
            if PRODUCTS_JSON.exists():
                with open(PRODUCTS_JSON, "r", encoding="utf-8") as f:
                    products = json.load(f)
            else:
                products = []

            # --- Generate unique product ID ---
            product_id = f"p{len(products)+1}"

            # --- Append new product ---
            new_product = {
                "id": product_id,
                "title": title,
                "price": price,
                "category": category,
                "image": unique_image_name,
                "stock": stock
            }
            products.append(new_product)

            # --- Save back to JSON ---
            with open(PRODUCTS_JSON, "w", encoding="utf-8") as f:
                json.dump(products, f, indent=2)

            st.success(f"Product '{title}' added successfully!")
