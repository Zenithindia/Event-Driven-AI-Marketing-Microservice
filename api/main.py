from fastapi import FastAPI, Depends, HTTPException, Response, Cookie
from pydantic import BaseModel
from celery import Celery
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import os

app = FastAPI(title="Smart Notification API with Database & Cookies")

# --- CORS SECURITY ---
# Must match your VS Code Live Server port!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    allow_credentials=True, 
    allow_methods=["*"],
    allow_headers=["*"],
)

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
celery_app = Celery("tasks", broker=CELERY_BROKER_URL)

# --- DATABASE SETUP ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./store.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- PAYLOADS ---
class LoginPayload(BaseModel):
    email: str
    name: str

class StoreEventPayload(BaseModel):
    email: str
    item: str

# --- AUTHENTICATION ENDPOINTS ---
@app.post("/login")
def login_user(payload: LoginPayload, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    
    if not user:
        user = User(email=payload.email, name=payload.name)
        db.add(user)
        db.commit()

    # Set the secure cookie
    response.set_cookie(
        key="store_session", 
        value=user.email, 
        httponly=True, 
        samesite="lax",
        max_age=604800 # 7 days
    )
    return {"status": "success", "message": f"Welcome, {user.name}!"}

@app.get("/me")
def check_if_logged_in(store_session: str = Cookie(None), db: Session = Depends(get_db)):
    if not store_session:
        raise HTTPException(status_code=401, detail="No cookie found.")
    
    user = db.query(User).filter(User.email == store_session).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid cookie.")
        
    return {"email": user.email, "name": user.name}

@app.post("/logout")
def logout_user(response: Response):
    # Delete the cookie
    response.delete_cookie(key="store_session", httponly=True, samesite="lax")
    return {"status": "success", "message": "Logged out."}

# --- WEBHOOK ENDPOINTS ---
@app.post("/webhook/cart_abandoned")
def handle_abandoned_cart(payload: StoreEventPayload, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    celery_app.send_task("tasks.process_abandoned_cart", kwargs={"email": user.email, "name": user.name, "item": payload.item})
    return {"status": "success"}

@app.post("/webhook/product_interest")
def handle_product_interest(payload: StoreEventPayload, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    celery_app.send_task("tasks.process_product_interest", kwargs={"email": user.email, "name": user.name, "item": payload.item})
    return {"status": "success"}