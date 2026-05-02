from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib
import os
from dotenv import load_dotenv

load_dotenv()

# ---------------- APP ----------------
app = FastAPI()

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change later to your frontend URL
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

# --------- EMAIL CONFIGURATION ---------
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
STORE_EMAIL = os.getenv("STORE_EMAIL")
CC_EMAIL = os.getenv("CC_EMAIL")
COPY_EMAILS = [email.strip() for email in os.getenv("COPY_EMAILS", "").split(",")]

# Email sending function
async def send_email(name: str, phone: str, sender_email: str, message: str):
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["Subject"] = f"New Form Submission from {name}"
        
        # Email body
        email_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>New Form Submission</h2>
                <p><strong>Name:</strong> {name}</p>
                <p><strong>Phone:</strong> {phone}</p>
                <p><strong>Email:</strong> {sender_email}</p>
                <p><strong>Message:</strong></p>
                <p>{message}</p>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(email_body, "html"))
        
        # Recipients: Store email (To), CC email, and 3 copy emails
        all_recipients = [STORE_EMAIL]
        if CC_EMAIL:
            msg["Cc"] = CC_EMAIL
            all_recipients.append(CC_EMAIL)
        
        all_recipients.extend(COPY_EMAILS)
        all_recipients = [e for e in all_recipients if e]  # Remove empty emails
        
        # Send email
        async with aiosmtplib.SMTP(hostname=SMTP_SERVER, port=SMTP_PORT) as smtp:
            await smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            await smtp.sendmail(SENDER_EMAIL, all_recipients, msg.as_string())
        
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False
@app.get("/")
def home():
    return {"message": "Backend Working"}

@app.get("/test")
def test():
    return {"status": "ok"}
@app.post("/submit")
async def submit_form(
    name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    message: str = Form(...)
):
    db = SessionLocal()
    try:
        new_data = FormData(name=name, phone=phone, email=email, message=message)
        db.add(new_data)
        db.commit()
        db.refresh(new_data)
        
        # Send email
        email_sent = await send_email(name, phone, email, message)
        
        return {
            "message": "Data saved successfully",
            "email_sent": email_sent,
            "id": new_data.id
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