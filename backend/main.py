from fastapi import FastAPI, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database setup
DATABASE_URL = "sqlite:///./form_data.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Model
class FormData(Base):
    __tablename__ = "form_data"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    phone = Column(String)
    email = Column(String, index=True)
    message = Column(Text)

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI()

# Mount static files
frontend_path = os.path.join(os.path.dirname(__file__), "../frontend")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    # Serve the index.html
    index_path = os.path.join(os.path.dirname(__file__), "../frontend/index.html")
    with open(index_path, "r") as f:
        return f.read()

@app.get("/second", response_class=HTMLResponse)
async def read_second():
    second_path = os.path.join(os.path.dirname(__file__), "../frontend/second.html")
    with open(second_path, "r") as f:
        return f.read()

@app.post("/submit")
async def submit_form(name: str = Form(...), phone: str = Form(...), email: str = Form(...), message: str = Form(...)):
    db = SessionLocal()
    try:
        form_entry = FormData(name=name, phone=phone, email=email, message=message)
        db.add(form_entry)
        db.commit()
        db.refresh(form_entry)
        return {"message": "Data saved successfully", "id": form_entry.id}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

@app.get("/data")
async def get_data():
    db = SessionLocal()
    try:
        data = db.query(FormData).all()
        return [{"id": item.id, "name": item.name, "phone": item.phone, "email": item.email, "message": item.message} for item in data]
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)