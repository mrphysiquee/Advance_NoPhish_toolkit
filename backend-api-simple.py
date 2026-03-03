#!/usr/bin/env python3
"""
NoPhish Professional Backend API - Simplified Version
Role-based access control and database management
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.exc import IntegrityError
import bcrypt
import jwt
from jwt.exceptions import PyJWTError
import redis
import uvicorn

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/nophish")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")

# Database setup
Base = declarative_base()

# Database Models
class UserRole(Base):
    __tablename__ = "user_roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # admin, user, viewer
    description = Column(String(255))
    permissions = Column(String)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role_id = Column(Integer, ForeignKey("user_roles.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    telegram_chat_id = Column(String(50))

class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    domain = Column(String(200), nullable=False)
    target_url = Column(String(500), nullable=False)
    num_users = Column(Integer, default=1)
    browser_type = Column(String(20), default='firefox')
    ssl_enabled = Column(Boolean, default=False)
    status = Column(String(20), default='created')
    admin_password = Column(String(100))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class CampaignSession(Base):
    __tablename__ = "campaign_sessions"
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    user_num = Column(Integer, nullable=False)
    container_name = Column(String(100), nullable=False)
    container_type = Column(String(20), nullable=False)
    status = Column(String(20), default='pending')
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime)
    browser = Column(String(20))  # For browser-specific logging

class SessionLog(Base):
    __tablename__ = "session_logs"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("campaign_sessions.id"))
    log_type = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    telegram_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Database connection
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# FastAPI app
app = FastAPI(
    title="NoPhish Professional API",
    description="Professional phishing platform with role-based access control",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://account-login.help", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Redis connection
try:
    redis_client = redis.from_url(REDIS_URL)
    redis_client.ping()
    print("Redis connected successfully")
except Exception as e:
    print(f"Redis connection failed: {e}")
    redis_client = None

# Pydantic models
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=80)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None
    role_id: Optional[int] = None

class UserLogin(BaseModel):
    username: str
    password: str

class CampaignCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    domain: str = Field(..., min_length=1, max_length=200)
    target_url: str = Field(..., pattern=r'^https?://')
    num_users: int = Field(1, ge=1, le=100)
    browser_type: str = Field('firefox', pattern=r'^(firefox|chrome)$')
    ssl_enabled: bool = False

class CampaignResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    domain: str
    target_url: str
    num_users: int
    browser_type: str
    ssl_enabled: bool
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# Utility functions
def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username

def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_current_user(db: Session = Depends(lambda: SessionLocal()), username: str = Depends(verify_token)):
    user = get_user(db, username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# API Endpoints
@app.get("/")
async def root():
    return {"message": "NoPhish Professional API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/auth/register", response_model=dict)
async def register(user: UserCreate, db: Session = Depends(lambda: SessionLocal())):
    # Check if user already exists
    if get_user(db, user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        full_name=user.full_name,
        role_id=user.role_id or 2  # Default to 'user' role
    )
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": db_user.id,
                "username": db_user.username,
                "email": db_user.email,
                "full_name": db_user.full_name,
                "role_id": db_user.role_id,
                "is_active": db_user.is_active
            }
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating user"
        )

@app.post("/auth/login", response_model=dict)
async def login(user: UserLogin, db: Session = Depends(lambda: SessionLocal())):
    db_user = get_user(db, user.username)
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    db_user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "full_name": db_user.full_name,
            "role_id": db_user.role_id,
            "is_active": db_user.is_active
        }
    }

@app.get("/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role_id": current_user.role_id,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login
    }

@app.get("/campaigns", response_model=List[CampaignResponse])
async def get_campaigns(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(lambda: SessionLocal())
):
    campaigns = db.query(Campaign).offset(skip).limit(limit).all()
    return campaigns

@app.post("/campaigns", response_model=CampaignResponse)
async def create_campaign(
    campaign: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(lambda: SessionLocal())
):
    # Check user permissions
    if current_user.role_id not in [1, 2]:  # admin or user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    db_campaign = Campaign(
        name=campaign.name,
        description=campaign.description,
        domain=campaign.domain,
        target_url=campaign.target_url,
        num_users=campaign.num_users,
        browser_type=campaign.browser_type,
        ssl_enabled=campaign.ssl_enabled,
        created_by=current_user.id
    )
    
    try:
        db.add(db_campaign)
        db.commit()
        db.refresh(db_campaign)
        return db_campaign
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating campaign"
        )

@app.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(lambda: SessionLocal())
):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Check permissions
    if current_user.role_id == 3 and campaign.created_by != current_user.id:  # viewer role
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return campaign

@app.get("/sessions")
async def get_sessions(
    campaign_id: Optional[int] = None,
    browser: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(lambda: SessionLocal())
):
    query = db.query(CampaignSession)
    
    if campaign_id:
        query = query.filter(CampaignSession.campaign_id == campaign_id)
    if browser:
        query = query.filter(CampaignSession.browser == browser)
    if status:
        query = query.filter(CampaignSession.status == status)
    
    sessions = query.offset(skip).limit(limit).all()
    return sessions

@app.get("/stats")
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(lambda: SessionLocal())
):
    # Get basic statistics
    total_campaigns = db.query(Campaign).count()
    total_sessions = db.query(CampaignSession).count()
    active_sessions = db.query(CampaignSession).filter(CampaignSession.status == 'active').count()
    
    # Get browser-specific statistics
    chrome_sessions = db.query(CampaignSession).filter(CampaignSession.browser == 'chrome').count()
    firefox_sessions = db.query(CampaignSession).filter(CampaignSession.browser == 'firefox').count()
    
    return {
        "total_campaigns": total_campaigns,
        "total_sessions": total_sessions,
        "active_sessions": active_sessions,
        "browser_stats": {
            "chrome": chrome_sessions,
            "firefox": firefox_sessions
        }
    }

@app.get("/notifications")
async def get_notifications(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(lambda: SessionLocal())
):
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    
    return notifications

# Telegram bot placeholder
@app.post("/telegram/webhook")
async def telegram_webhook(update: dict, background_tasks: BackgroundTasks):
    """Placeholder for Telegram webhook handling"""
    # Process Telegram updates here
    background_tasks.add_task(process_telegram_update, update)
    return {"status": "ok"}

def process_telegram_update(update: dict):
    """Process Telegram updates"""
    # Implement Telegram bot logic here
    print(f"Processing Telegram update: {update}")

# Initialize database
def init_db():
    print("Initializing database...")
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully")

if __name__ == "__main__":
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=5000)