# ===============================
# utils.py
# Helper functions for Fake Shopify (Fixed)
# ===============================

import hashlib
import uuid
import json
from datetime import datetime
from db import get_conn
from pathlib import Path
import smtplib
import ssl
import random

# -----------------------------
# 🔐 Secure Password Hashing
# -----------------------------
def hash_password(password: str) -> str:
    """Password ko SHA256 hash me convert karta hai."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# -----------------------------
# 👤 Create User (Safe insert)
# -----------------------------
def create_user(email: str, name: str, password: str) -> bool:
    """
    Create new user.
    Return True if success, False if email exists or error.
    """
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT email FROM users WHERE email=?", (email,))
    if c.fetchone():
        conn.close()
        return False
    hashed = hash_password(password)
    try:
        c.execute(
            """
            INSERT INTO users (email, name, password_hash, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (email, name, hashed, datetime.now().isoformat())
        )
        conn.commit()
        return True
    except Exception as e:
        print("Error inserting user:", e)
        return False
    finally:
        conn.close()


#--------------------------------
# Save login user 
#--------------------------------
def save_login_log(email):
    """Save login history"""
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO login_logs (email, login_time) VALUES (?, ?)",
        (email, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


# -----------------------------
# 🔑 Verify Login Credentials
# -----------------------------
def verify_user(email: str, password: str) -> bool:
    """Check email+password against DB"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE email=?", (email,))
    row = c.fetchone()
    conn.close()
    if not row:
        return False
    return row["password_hash"] == hash_password(password)


# -----------------------------
# 🧾 Generate Unique Invoice ID
# -----------------------------
def generate_invoice_id() -> str:
    """Generate unique 12-char invoice ID"""
    return uuid.uuid4().hex[:12].upper()


# -----------------------------
# 🌐 Persistent Login Helpers
# -----------------------------
SESSION_FILE = Path("user_session.json")

def auto_login() -> str | None:
    """Return logged-in email from local session file"""
    if SESSION_FILE.exists():
        try:
            data = json.loads(SESSION_FILE.read_text())
            return data.get("email")
        except Exception:
            return None
    return None

def save_login(email: str):
    """Save login to local session file"""
    SESSION_FILE.write_text(json.dumps({"email": email}))

def logout_user():
    """Delete session file to logout"""
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()


# -----------------------------
# 📧 Email & OTP Setup
# -----------------------------
email_sender = "samadrao318@gmail.com"         # Tumhara Gmail
app_password = "vsta dqca bznh jpyd"           # 16-char App Password generated
OTP_FILE = Path("otp_store.json")


# -----------------------------
# 🔹 OTP Email Login Helpers
# -----------------------------
def send_otp_email(to_email: str) -> bool:
    """
    Generate 6-digit OTP and send to user email.
    Returns True if sent, False if error.
    """
    otp = random.randint(100000, 999999)
    # Save OTP locally
    OTP_FILE.write_text(json.dumps({"email": to_email, "otp": otp}))

    subject = "Your OTP Code"
    body = f"Your OTP is: {otp}"
    email_message = f"Subject: {subject}\n\n{body}"

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(email_sender, app_password)
            server.sendmail(email_sender, to_email, email_message)
        return True
    except Exception as e:
        print("Failed to send OTP:", e)
        return False


def verify_otp(email: str, user_otp: str) -> bool:
    """Check OTP correctness"""
    if not OTP_FILE.exists():
        return False
    try:
        data = json.loads(OTP_FILE.read_text())
        return data["email"] == email and str(data["otp"]) == str(user_otp)
    except Exception:
        return False


def otp_clear():
    """Clear OTP after verification"""
    if OTP_FILE.exists():
        OTP_FILE.unlink()
