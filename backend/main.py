from fastapi import FastAPI, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from fastapi.middleware.cors import CORSMiddleware

# ✅ Create app FIRST
app = FastAPI()

# ✅ CORS (after app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later restrict
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- DB SETUP ----------------
DATABASE_URL = "sqlite:///./form_data.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Model
class FormData(Base):
    __tablename__ = "form_data"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    phone = Column(String)
    email = Column(String)
    message = Column(Text)

Base.metadata.create_all(bind=engine)

# ---------------- FRONTEND PATH ----------------
frontend_path = os.path.join(os.path.dirname(__file__), "../frontend")

app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# ---------------- ROUTES ----------------
@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open(os.path.join(frontend_path, "index.html")) as f:
        return f.read()

@app.get("/second", response_class=HTMLResponse)
async def read_second():
    with open(os.path.join(frontend_path, "second.html")) as f:
        return f.read()

@app.post("/submit")
async def submit_form(
    name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    message: str = Form(...)
):
    db = SessionLocal()
    try:
        form_entry = FormData(name=name, phone=phone, email=email, message=message)
        db.add(form_entry)
        db.commit()
        db.refresh(form_entry)
        return {"message": "Saved", "id": form_entry.id}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

@app.get("/data")
async def get_data():
    db = SessionLocal()
    data = db.query(FormData).all()
    db.close()
    return data