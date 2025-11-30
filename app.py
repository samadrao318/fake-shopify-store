# app.py
# Main Streamlit app for Fake Shopify Dashboard with local product folder and login requirement

from pathlib import Path
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

# IMPORTANT: set_page_config must be the first Streamlit command after import
st.set_page_config(page_title="Fake Shopify Dashboard", layout="wide")

#from db import init_db, load_products_from_json, save_order, get_orders_df,save_user

from utils import verify_user, save_login, save_login_log, send_otp_email, verify_otp, otp_clear
from utils import create_user, verify_user, generate_invoice_id, auto_login, save_login, logout_user,save_login_log
from db import init_db, save_user, get_user, save_order, get_orders_df, load_products_from_json
from admin import admin_page
# VERY IMPORTANT

# init DB
init_db()




# constants
PRODUCTS_JSON = Path("products/products.json")
PRODUCTS_IMG_DIR = Path("products/images")

# session init
if "user" not in st.session_state:
    st.session_state.user = None
if "cart" not in st.session_state:
    st.session_state.cart = {}

if st.session_state.user is None:
    st.session_state.user = auto_login()


# load products
products = load_products_from_json(PRODUCTS_JSON)

# helper to map id->product
prod_map = {p["id"]: p for p in products}

#save  sign up page
def user_page():
    st.title("Fake Shopify")
    if st.session_state.user:
        # st.subheader(f"**{name}** sign_up")
        # st.dataframe(tab)
        st.write("👨🏻‍💼 Logged in as: /n ", f" **{st.session_state.user}**")
        if st.button("Logout", type="primary", key="ss"):
            st.session_state.user = None
            st.rerun()

    else:
        st.header("User Sign_up ")
        st.caption("Create Account")
        with st.form("User From"):
            name = st.text_input("Enter the Name:", placeholder="Enter name here")
            email = st.text_input("Enter Email", placeholder="example@gmail.com")
            age = st.number_input("Enter age " ,min_value=15, max_value=120, value=20)
            pas = st.text_input("Enter Passward", placeholder= "passward")
            submit = st.form_submit_button("Submit" , type="primary" , key = "s")

        email1 = email.endswith("@gmail.com")
        if submit:
            if not name  or not email or not age or not pas:
                st.error("Filled all format are complete")
            elif  len(pas) < 8 :
                st.error("Must be 8 Charcter in passward")
            elif not email1:
                st.error("Enter correct emial")
            elif age < 15 :
                st.error("Age must be 15 plus then you are illigible")
            else:
                hidden_pasw= "*"*len(pas)
                st.success(f"""From submitted successfully :\n
                    Name : {name}\n
                    Email : {email}\n
                    Age : {age}\n
                    passward : {hidden_pasw}""")
                ok = create_user(email, name, pas)
                if ok:
                    st.success("Account created — please login")
                else:
                    st.error("Could not create account (maybe email taken)")
        # else:
        #     st.error("Enter submitted button thank you!")



# login email logic
from db import get_conn

def user_login():
    st.header("LOGIN USER")

    # ---------------------
    # Auto-login check
    # ---------------------
    if "user" not in st.session_state:
        st.session_state.user = auto_login()  # Load from session file if exists

    if "user" in st.session_state and st.session_state.user:
        st.success(f"Already logged in as {st.session_state.user}")
        if st.button("Logout"):
            logout_user()
            st.session_state.clear()  # Clear all session state
            st.rerun()
        return

    # ---------------------
    # Email input
    # ---------------------
    email = st.text_input("Email", placeholder="example@gmail.com", key="login_email")

    # ---------------------
    # Step 1: Send OTP
    # ---------------------
    if st.button("Send OTP"):
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT email FROM users WHERE email=?", (email.lower(),))
        user = c.fetchone()
        conn.close()

        if not user:
            st.error("This email is not registered.")
        else:
            try:
                send_otp_email(email)
                st.session_state.temp_email = email.lower()  # always lower case
                st.success("OTP sent to your email! Please enter below.")
            except Exception as e:
                st.error(f"Failed to send OTP. Please check email or try later.\nError: {e}")

    # ---------------------
    # Step 2: Verify OTP
    # ---------------------
    if "temp_email" in st.session_state:
        otp_input = st.text_input("Enter OTP", max_chars=6, key="otp_input")
        if st.button("Verify OTP"):
            if verify_otp(st.session_state.temp_email, otp_input):
                # OTP correct → set session
                st.session_state.user = st.session_state.temp_email
                st.session_state.logged_in = True
                save_login(st.session_state.user)
                save_login_log(st.session_state.user)
                otp_clear()
                st.success(f"Login successful as {st.session_state.user}")
                st.rerun()
            else:
                st.error("Invalid OTP!")


            
# --- Layout: sidebar (login/signup + navigation) ---
with st.sidebar:
    if "email" in st.session_state:
        st.sidebar.write(f"Logged in as: {st.session_state['email']}")

        if st.session_state["email"] == "admin@gmail.com":
            st.sidebar.page_link("pages/admin.py", label="🛠️ Admin Panel")

    if st.session_state.user:
        st.write(f"👨🏻‍💼 Logged in as: **{st.session_state.user}**")
        if st.button("Logout", key="{id}", type="primary"):
            st.session_state.user = None
            logout_user()
            st.success("Logged out")
            st.markdown("---")
            st.rerun()
            

    # else:
    #     st.write("### Login / Sign_up")
    #     tab = st.radio("", ["Login", "Sign_up"], index=0)
    #     if tab == "Sign_up":
    #         s_name = st.text_input("Name", key="signup_name")
    #         s_email = st.text_input("Email", key="signup_email")
    #         s_pass = st.text_input("Password", type="password", key="signup_pass")
    #         if st.button("Create Account"):
    #             ok = create_user(s_email, s_name, s_pass)
    #             if ok:
    #                 st.success("Account created — please login")
    #             else:
    #                 st.error("Could not create account (maybe email taken)")
    #     else:
    #         l_email = st.text_input("Email", key="login_email")
    #         l_pass = st.text_input("Password", type="password", key="login_pass")
    #         if st.button("Login"):
    #             if verify_user(l_email, l_pass):
    #                 st.session_state.user = l_email
    #                 st.success("Logged in")
    #                 st.rerun()
    #             else:
    #                 st.error("Invalid credentials")
    # tab = st.selectbox("Sign_up / Login" ,["All","Sign_up","Login"])
    # st.session_state.page = tab
    
    
    if st.session_state.user == "samadrao318@gmail.com":
        nav = st.radio("Navigation", ["Store", "Orders", "Dashboard","Sign_up","Login" ,"Admin"], index=0)
    else:  
        nav = st.radio("Navigation", ["Store", "Orders", "Dashboard","Sign_up","Login" ], index=0)  
    st.session_state.page = nav
    st.markdown("---")
    st.write(f"Cart items: {sum(st.session_state.cart.values())}")
    st.markdown("---")
    st.write("© Rao Samad | Built for learning & real use")
# --- Store Page ---
def show_store():
    st.title("Product Store 👕")
    st.caption("All product are here.")
    col1 , col2 = st.columns(2)
    with col1:
        st.header("Select prodect")
        for p in products:
            st.image(str(PRODUCTS_IMG_DIR / p["image"]), width=240)
            st.subheader(p["title"])
            st.write(f'Category: {p["category"]}  |  Price: ${p["price"]}  |  Stock: {p["stock"]}')
            if st.button(f"View / Select - {p['title']}", key=f"view_{p['id']}"):
                # require login before viewing details / selecting
                if not st.session_state.user:
                    st.warning("You must login to view product details and order.")
                else:
                    st.session_state.selected_product = p["id"]
                    st.rerun()
            st.markdown("---")

    with col2:
        st.header("Cart 🛒")
        if st.session_state.cart:
            df_cart = []
            total = 0
            for pid, qty in st.session_state.cart.items():
                pr = prod_map.get(pid)
                line = {"title": pr["title"], "qty": qty, "line_total": pr["price"]*qty}
                total += line["line_total"]
                df_cart.append(line)
            st.table(pd.DataFrame(df_cart))
            st.success(f"**Total: ${total:.2f}**")
            if st.button("Checkout", key = "primary"):
                if not st.session_state.user:
                    st.error("Login required to checkout.")
                else:
                    # create order
                    invoice = generate_invoice_id()
                    items = []
                    for pid, qty in st.session_state.cart.items():
                        pr = prod_map[pid]
                        items.append({"id": pid, "title": pr["title"], "price": pr["price"], "qty": qty})
                    save_order(invoice, st.session_state.user, items, total, status="PLACED")
                    st.success(f"Order placed — Invoice: {invoice}")
                    st.session_state.cart = {}
        else:
            st.info("Cart is empty")
        st.markdown("---")
        st.write("© Rao Samad | Built for learning & real use")
# --- Selected product detail (requires login) ---
def show_product_detail(pid):
    p = prod_map[pid]
    st.header(p["title"])
    st.image(str(PRODUCTS_IMG_DIR / p["image"]), width=320)
    st.write(f'Category: {p["category"]}')
    st.write(f'Price: ${p["price"]}')
    st.write(f'Stock: {p["stock"]}')
    qty = st.number_input("Quantity", min_value=1, max_value=p["stock"], value=1, key=f"qty_sel_{pid}")
    if st.button("Add to cart and return to Store"):
        st.session_state.cart[pid] = st.session_state.cart.get(pid, 0) + qty
        st.success("Added to cart")
        st.session_state.selected_product = None
        st.rerun()



# --- Orders page ---
def show_orders():
    st.title("Orders 🛍️🛒")
    df = get_orders_df()
    if df.empty:
        st.info("No orders yet")
        return

    st.subheader("Check your order")

    # --- SEARCH BOX ---
    query = st.text_input("Enter your Email or Invoice ID", placeholder="Email / Invoice ID")

    if query:
        # case-insensitive search
        filtered = df[
            df["customer_email"].str.contains(query, case=False, na=False) |
            df["invoice_id"].str.contains(query, case=False, na=False)
        ]

        if filtered.empty:
            st.warning("No matching order found.")
        else:
            st.success("Your Orders:")
            st.dataframe(filtered)
            return  # stop here, don't show full list

    # ---- FULL LIST OF ORDERS ----
    st.dataframe(
        df[["invoice_id", "created_at", "customer_email", "total", "status"]]
        .sort_values("created_at", ascending=False)
    )

    # ---- CANCEL ORDER ----
    st.markdown("---")
    st.subheader("Cancel your order (within 5 hours)")
    
    cid = st.text_input("Invoice ID to cancel", placeholder="Enter invoice id", key="cancel_input")
    
    if st.button("Cancel Order"):
        if not st.session_state.user:
            st.error("Login required")
        else:
            row = df[(df.invoice_id==cid) & (df.customer_email==st.session_state.user)]
            if row.empty:
                st.error("Order not found or not yours")
            else:
                created = row.iloc[0]["created_at"]
                if (datetime.now() - created.to_pydatetime()) > timedelta(hours=5):
                    st.error("Cannot cancel — 5 hours passed")
                else:
                    conn = __import__("sqlite3").connect("fake_shop.db")
                    c = conn.cursor()
                    c.execute("UPDATE orders SET status='CANCELLED' WHERE invoice_id=?", (cid,))
                    conn.commit()
                    conn.close()
                    st.success("Order cancelled")


# --- Dashboard page ---
def show_dashboard():
    st.header("📊 Dashboard ")
    df = get_orders_df()
    if df.empty:
        st.info("No orders yet")
        return

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        date_from = st.date_input("From", value=(datetime.now() - timedelta(days=30)).date())
    with col2:
        date_to = st.date_input("To", value=datetime.now().date())

    mask = (df["created_at"].dt.date >= date_from) & (df["created_at"].dt.date <= date_to)
    filtered = df[mask].copy()
    
    st.divider()
    col1 ,col2 = st.columns(2)
    
    col1.metric("**Total Sales**", f"${filtered['total'].sum():.2f}")
    col2.metric("**Orders**", f"{len(filtered)}✔")

    # Time series
    ts = filtered.set_index("created_at").resample("D").sum()["total"].reset_index()
    fig = px.line(ts, x="created_at", y="total", title="📈 Sales Over Time")
    st.plotly_chart(fig, use_container_width=True)

    
    
    # Top 10 products
    all_items = []
    for items in filtered["items_json"].apply(json.loads):
        all_items.extend(items)
    items_df = pd.DataFrame(all_items)
    if not items_df.empty:
        top = items_df.groupby("title").agg({"qty":"sum", "price":"mean"}).reset_index()
        top["revenue"] = top["qty"]*top["price"]
        top = top.sort_values("qty", ascending=False)
        st.subheader("Top Products")
        st.dataframe(top.head(10))
        fig2 = px.bar(top.head(10), x="title", y="qty", title="🔝 Top 10 Products by Quantity")
        st.plotly_chart(fig2, use_container_width=True)
    
    
    #st.dataframe(filtered)
    
# --- Main render logic ---
if st.session_state.get("selected_product"):
    # Show selected product detail when chosen
    show_product_detail(st.session_state.selected_product)
    
elif st.session_state.user == "samadrao318@gmail.com":
    page = st.session_state.get("page", "Store")
    if page == "Store":
        show_store()
    elif page == "Orders":
        show_orders() 
    elif page == "Dashboard":
        show_dashboard()
    elif page == "Sign_up":
        user_page()
    elif page == "Login":
        user_login()
    elif page == "Admin":
        admin_page()
    
else:
    page = st.session_state.get("page", "Store")
    
    if page == "Store":
        show_store()
    elif page == "Orders":
        show_orders() 
    elif page == "Dashboard":
        show_dashboard()
    elif page == "Sign_up":
        user_page()
    elif page == "Login":
        user_login() 




# if st.session_state.get("selected_product"):
#     # Show selected product detail when chosen
#     show_product_detail(st.session_state.selected_product)
# else:
#     tab = st.session_state.get("page", "All")
# if tab == "All":
#     user_page()
# elif tab == "Sign_up":
#     user_page()
# elif tab == "Login":
