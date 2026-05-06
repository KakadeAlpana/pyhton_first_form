from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
import os

load_dotenv(Path(__file__).with_name(".env"))

# ---------------- APP ----------------
app = FastAPI()

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- DATABASE ----------------
DATABASE_URL = "sqlite:///./form_data.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class FormData(Base):
    __tablename__ = "form_data"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    phone = Column(String)
    email = Column(String)
    message = Column(Text)


Base.metadata.create_all(bind=engine)


# ---------------- EMAIL FUNCTION ----------------
def send_email(site, name, phone, user_email, message):
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    sender_email = os.getenv("SENDER_EMAIL")
    app_password = os.getenv("SENDER_PASSWORD")
    receiver_email = os.getenv("STORE_EMAIL", "alpana.pawar89@gmail.com")

    if not sender_email or not app_password:
        error = "Email credentials not set"
        print(error)
        return False, error

    body = f"""
New form submission

Website: {site}
Name: {name}
Phone: {phone}
User Email: {user_email}
Message: {message}
"""

    msg = MIMEText(body)
    msg["Subject"] = f"New Contact Form - Site {site}"
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Reply-To"] = user_email

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.send_message(msg)

        print(f"Email sent to {receiver_email}")
        return True, None

    except Exception as e:
        error = str(e)
        print("Email error:", error)
        return False, error


# ---------------- ROUTES ----------------
@app.get("/")
def home():
    return {"message": "Backend Working"}


@app.post("/submit")
def submit_form(
    site: str = Form(...),
    name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    message: str = Form(...)
):
    db = SessionLocal()

    try:
        new_data = FormData(
            name=name,
            phone=phone,
            email=email,
            message=message
        )
        db.add(new_data)
        db.commit()
        db.refresh(new_data)

        email_sent, email_error = send_email(site, name, phone, email, message)

        return {
            "message": "Data saved successfully",
            "email_sent": email_sent,
            "email_error": email_error
        }

    except Exception as e:
        db.rollback()
        return {"error": str(e)}

    finally:
        db.close()


@app.get("/data")
def get_data():
    db = SessionLocal()
    data = db.query(FormData).all()
    db.close()
    return data
