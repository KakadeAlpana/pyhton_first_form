from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import smtplib
from email.mime.text import MIMEText
import os

# ---------------- APP ----------------
app = FastAPI()

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to frontend URL later
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
def send_email(name, phone, email, message):
    try:
        sender_email = os.getenv("EMAIL_USER")
        app_password = os.getenv("EMAIL_PASS")

        if not sender_email or not app_password:
            print("Email credentials not set")
            return

        receiver_email = sender_email  # fixed receiver

        msg = MIMEText(
            f"New Form Submission\n\n"
            f"Name: {name}\n"
            f"Phone: {phone}\n"
            f"Email: {email}\n"
            f"Message: {message}"
        )
        msg["Subject"] = "New Contact Form Submission"
        msg["From"] = sender_email
        msg["To"] = receiver_email

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.send_message(msg)
        server.quit()

        print("Email sent successfully")

    except Exception as e:
        print("Email error:", e)  # won't crash app

# ---------------- ROUTES ----------------

@app.get("/")
def home():
    return {"message": "Backend Working"}

@app.post("/submit")
def submit_form(
    name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    message: str = Form(...)
):
    db = SessionLocal()

    try:
        # Save to DB
        new_data = FormData(
            name=name,
            phone=phone,
            email=email,
            message=message
        )
        db.add(new_data)
        db.commit()
        db.refresh(new_data)

        # Send email (safe)
        send_email(name, phone, email, message)

        return {"message": "Data saved successfully"}

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