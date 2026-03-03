#!/usr/bin/env python3
"""
NoPhish Professional Backend API with Telegram Bot Integration
Role-based access control and database management
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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
import docker


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
    permissions = Column(Text)  # JSON string of permissions

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
    telegram_chat_id = Column(String(50), nullable=True)
    
    role = relationship("UserRole")

class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    domain = Column(String(200), nullable=False)
    target_url = Column(String(500), nullable=False)
    num_users = Column(Integer, default=1)
    browser_type = Column(String(20), default="firefox")  # firefox, chrome
    ssl_enabled = Column(Boolean, default=False)
    status = Column(String(20), default="created")  # created, running, stopped
    admin_password = Column(String(100))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    creator = relationship("User")
    sessions = relationship("CampaignSession", back_populates="campaign")

class CampaignSession(Base):
    __tablename__ = "campaign_sessions"
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    user_num = Column(Integer, nullable=False)
    container_name = Column(String(100), nullable=False)
    container_type = Column(String(20), nullable=False)  # desktop, mobile
    status = Column(String(20), default="pending")  # pending, running, disconnected
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime)
    
    campaign = relationship("Campaign", back_populates="sessions")

class SessionLog(Base):
    __tablename__ = "session_logs"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("campaign_sessions.id"))
    log_type = Column(String(20), nullable=False)  # session, cookie, keylog
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String(50), nullable=False)  # campaign_created, session_captured, etc.
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    telegram_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic Models
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=80)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None
    role_id: Optional[int] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role_name: str
    is_active: bool
    created_at: datetime
    telegram_chat_id: Optional[str]

    class Config:
        from_attributes = True

class CampaignCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    domain: str = Field(..., min_length=1)
    target_url: str = Field(..., regex=r'^https?://')
    num_users: int = Field(1, ge=1, le=100)
    browser_type: str = Field("firefox", regex=r'^(firefox|chrome)$')
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
    admin_password: Optional[str]
    created_by: str
    created_at: datetime
    updated_at: datetime
    sessions_count: int = 0

    class Config:
        from_attributes = True

class TelegramCommand(BaseModel):
    command: str
    args: List[str] = []

class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[Dict] = None
    callback_query: Optional[Dict] = None

# Database connection
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
redis_client = redis.from_url(REDIS_URL)

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize roles
def init_roles():
    db = SessionLocal()
    try:
        # Create default roles
        roles = [
            UserRole(name="admin", description="Full system access", permissions=json.dumps({
                "users": ["create", "read", "update", "delete"],
                "campaigns": ["create", "read", "update", "delete"],
                "monitoring": ["read", "write"],
                "system": ["read", "write"]
            })),
            UserRole(name="user", description="Standard user access", permissions=json.dumps({
                "users": ["read"],
                "campaigns": ["create", "read", "update", "delete"],
                "monitoring": ["read"],
                "system": ["read"]
            })),
            UserRole(name="viewer", description="Read-only access", permissions=json.dumps({
                "users": ["read"],
                "campaigns": ["read"],
                "monitoring": ["read"],
                "system": ["read"]
            }))
        ]
        
        for role in roles:
            existing = db.query(UserRole).filter(UserRole.name == role.name).first()
            if not existing:
                db.add(role)
        
        db.commit()
        print("✅ Roles initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing roles: {e}")
        db.rollback()
    finally:
        db.close()

# FastAPI app
app = FastAPI(
    title="NoPhish Professional API",
    description="NoPhish Professional Backend API with Telegram Bot Integration",
    version="1.0.0"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency to get current user
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Dependency to check permissions
def check_permission(user: User, resource: str, action: str):
    if not user.role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User role not assigned")
    
    permissions = json.loads(user.role.permissions)
    if resource not in permissions:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Resource not allowed")
    
    if action not in permissions[resource]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Action not allowed")

# Authentication functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Telegram Bot (placeholder for future implementation)
class TelegramBotManager:
    def __init__(self):
        self.bot = None
        print("🤖 Telegram bot integration - placeholder mode")
    
    async def start(self):
        if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
            print("⚠️  Telegram bot token not configured")
            return
        
        print("✅ Telegram bot placeholder started")
    
    async def handle_message(self, update):
        # Placeholder for Telegram message handling
        print(f"📨 Telegram message received: {update}")
        pass
    
    async def handle_start(self, chat_id, args):
        print(f"🎯 Telegram handle_start called for chat_id: {chat_id}")
        pass
    
    async def handle_help(self, chat_id, args):
        print(f"📖 Telegram handle_help called for chat_id: {chat_id}")
        pass
    
    async def handle_campaigns(self, chat_id, args):
        db = SessionLocal()
        try:
            # Find user by telegram chat ID
            user = db.query(User).filter(User.telegram_chat_id == str(chat_id)).first()
            if not user:
                await self.bot.send_message(chat_id, "Please link your account first using /settings")
                return
            
            campaigns = db.query(Campaign).filter(Campaign.created_by == user.id).all()
            
            if not campaigns:
                await self.bot.send_message(chat_id, "No campaigns found")
                return
            
            response = "📋 Your Campaigns:\n\n"
            for campaign in campaigns:
                response += f"🎯 {campaign.name} (ID: {campaign.id})\n"
                response += f"   Status: {campaign.status}\n"
                response += f"   Domain: {campaign.domain}\n"
                response += f"   Browser: {campaign.browser_type}\n\n"
            
            await self.bot.send_message(chat_id, response)
        except Exception as e:
            await self.bot.send_message(chat_id, "Error fetching campaigns")
        finally:
            db.close()
    
    async def handle_monitor(self, chat_id, args):
        if not args:
            await self.bot.send_message(chat_id, "Usage: /monitor <campaign_id>")
            return
        
        campaign_id = args[0]
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_chat_id == str(chat_id)).first()
            if not user:
                await self.bot.send_message(chat_id, "Please link your account first using /settings")
                return
            
            campaign = db.query(Campaign).filter(Campaign.id == campaign_id, Campaign.created_by == user.id).first()
            if not campaign:
                await self.bot.send_message(chat_id, "Campaign not found")
                return
            
            sessions = db.query(CampaignSession).filter(CampaignSession.campaign_id == campaign_id).all()
            active_sessions = [s for s in sessions if s.status == "running"]
            
            response = f"🎯 Monitoring Campaign: {campaign.name}\n\n"
            response += f"Status: {campaign.status}\n"
            response += f"Total Sessions: {len(sessions)}\n"
            response += f"Active Sessions: {len(active_sessions)}\n"
            response += f"Browser: {campaign.browser_type}\n"
            response += f"Domain: {campaign.domain}\n"
            
            await self.bot.send_message(chat_id, response)
        except Exception as e:
            await self.bot.send_message(chat_id, "Error monitoring campaign")
        finally:
            db.close()
    
    async def handle_sessions(self, chat_id, args):
        if not args:
            await self.bot.send_message(chat_id, "Usage: /sessions <campaign_id>")
            return
        
        campaign_id = args[0]
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_chat_id == str(chat_id)).first()
            if not user:
                await self.bot.send_message(chat_id, "Please link your account first using /settings")
                return
            
            campaign = db.query(Campaign).filter(Campaign.id == campaign_id, Campaign.created_by == user.id).first()
            if not campaign:
                await self.bot.send_message(chat_id, "Campaign not found")
                return
            
            sessions = db.query(CampaignSession).filter(CampaignSession.campaign_id == campaign_id).all()
            
            response = f"📊 Sessions for {campaign.name}:\n\n"
            for session in sessions[:10]:  # Show first 10 sessions
                response += f"Session {session.user_num} ({session.container_type}): {session.status}\n"
                if session.ip_address:
                    response += f"   IP: {session.ip_address}\n"
                response += "\n"
            
            if len(sessions) > 10:
                response += f"... and {len(sessions) - 10} more sessions"
            
            await self.bot.send_message(chat_id, response)
        except Exception as e:
            await self.bot.send_message(chat_id, "Error fetching sessions")
        finally:
            db.close()
    
    async def handle_keylogs(self, chat_id, args):
        await self.bot.send_message(chat_id, "🔒 Keylogs feature coming soon!")
    
    async def handle_stop(self, chat_id, args):
        if not args:
            await self.bot.send_message(chat_id, "Usage: /stop <campaign_id>")
            return
        
        campaign_id = args[0]
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_chat_id == str(chat_id)).first()
            if not user:
                await self.bot.send_message(chat_id, "Please link your account first using /settings")
                return
            
            campaign = db.query(Campaign).filter(Campaign.id == campaign_id, Campaign.created_by == user.id).first()
            if not campaign:
                await self.bot.send_message(chat_id, "Campaign not found")
                return
            
            # Update campaign status
            campaign.status = "stopped"
            db.commit()
            
            await self.bot.send_message(chat_id, f"✅ Campaign '{campaign.name}' stopped successfully")
        except Exception as e:
            await self.bot.send_message(chat_id, "Error stopping campaign")
        finally:
            db.close()
    
    async def handle_status(self, chat_id, args):
        if not args:
            await self.bot.send_message(chat_id, "Usage: /status <campaign_id>")
            return
        
        campaign_id = args[0]
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_chat_id == str(chat_id)).first()
            if not user:
                await self.bot.send_message(chat_id, "Please link your account first using /settings")
                return
            
            campaign = db.query(Campaign).filter(Campaign.id == campaign_id, Campaign.created_by == user.id).first()
            if not campaign:
                await self.bot.send_message(chat_id, "Campaign not found")
                return
            
            sessions = db.query(CampaignSession).filter(CampaignSession.campaign_id == campaign_id).all()
            active_sessions = [s for s in sessions if s.status == "running"]
            
            response = f"📊 Campaign Status: {campaign.name}\n\n"
            response += f"ID: {campaign.id}\n"
            response += f"Status: {campaign.status}\n"
            response += f"Created: {campaign.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            response += f"Total Sessions: {len(sessions)}\n"
            response += f"Active Sessions: {len(active_sessions)}\n"
            response += f"Browser: {campaign.browser_type}\n"
            response += f"Domain: {campaign.domain}\n"
            
            await self.bot.send_message(chat_id, response)
        except Exception as e:
            await self.bot.send_message(chat_id, "Error fetching status")
        finally:
            db.close()
    
    async def handle_settings(self, chat_id, args):
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_chat_id == str(chat_id)).first()
            
            if user:
                response = f"🔧 Account Settings:\n\n"
                response += f"Username: {user.username}\n"
                response += f"Email: {user.email}\n"
                response += f"Role: {user.role.name if user.role else 'Not assigned'}\n"
                response += f"Telegram: Linked ✅\n"
                await self.bot.send_message(chat_id, response)
            else:
                # Link account process
                keyboard = {
                    "inline_keyboard": [
                        [
                            {"text": "Link Account", "callback_data": "link_account"}
                        ]
                    ]
                }
                await self.bot.send_message(
                    chat_id,
                    "🔗 Link your NoPhish account to Telegram:\n\n"
                    "1. Go to NoPhish web interface\n"
                    "2. Go to Settings → Telegram Integration\n"
                    "3. Enter this chat ID: " + str(chat_id),
                    reply_markup=keyboard
                )
        except Exception as e:
            await self.bot.send_message(chat_id, "Error accessing settings")
        finally:
            db.close()
    
    async def handle_logout(self, chat_id, args):
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_chat_id == str(chat_id)).first()
            if user:
                user.telegram_chat_id = None
                db.commit()
                await self.bot.send_message(chat_id, "👋 Logged out successfully")
            else:
                await self.bot.send_message(chat_id, "No account linked to this chat")
        except Exception as e:
            await self.bot.send_message(chat_id, "Error logging out")
        finally:
            db.close()

# Initialize Telegram bot manager
telegram_manager = TelegramBotManager()

# API Endpoints

@app.get("/")
async def root():
    return {"message": "NoPhish Professional API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.post("/auth/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
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
        return {"message": "User registered successfully", "user_id": db_user.id}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Registration failed")

@app.post("/auth/login")
async def login(user_credentials: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_credentials.username).first()
    
    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User account is disabled")
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }

@app.get("/auth/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return UserResponse.from_orm(current_user)

@app.post("/telegram/link")
async def link_telegram_account(chat_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user.telegram_chat_id = str(chat_id)
    db.commit()
    
    # Send confirmation message via Telegram
    if telegram_manager.bot:
        try:
            await telegram_manager.bot.send_message(
                chat_id,
                f"✅ Account linked successfully!\n"
                f"Welcome, {current_user.username}!\n\n"
                f"Use /help to see available commands."
            )
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
    
    return {"message": "Telegram account linked successfully"}

@app.get("/users")
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_permission(current_user, "users", "read")
    
    users = db.query(User).offset(skip).limit(limit).all()
    return {"users": [UserResponse.from_orm(user) for user in users]}

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_permission(current_user, "users", "read")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse.from_orm(user)

@app.post("/campaigns")
async def create_campaign(
    campaign: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_permission(current_user, "campaigns", "create")
    
    db_campaign = Campaign(
        name=campaign.name,
        description=campaign.description,
        domain=campaign.domain,
        target_url=campaign.target_url,
        num_users=campaign.num_users,
        browser_type=campaign.browser_type,
        ssl_enabled=campaign.ssl_enabled,
        admin_password=os.urandom(16).hex(),  # Generate random admin password
        created_by=current_user.id
    )
    
    try:
        db.add(db_campaign)
        db.commit()
        db.refresh(db_campaign)
        
        # Send notification to Telegram if linked
        await send_telegram_notification(
            current_user.telegram_chat_id,
            "campaign_created",
            f"New campaign created: {campaign.name}",
            f"Campaign ID: {db_campaign.id}\nBrowser: {campaign.browser_type}"
        )
        
        return CampaignResponse.from_orm(db_campaign)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Failed to create campaign")

@app.get("/campaigns")
async def get_campaigns(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_permission(current_user, "campaigns", "read")
    
    if current_user.role.name == "admin":
        campaigns = db.query(Campaign).offset(skip).limit(limit).all()
    else:
        campaigns = db.query(Campaign).filter(Campaign.created_by == current_user.id).offset(skip).limit(limit).all()
    
    campaign_responses = []
    for campaign in campaigns:
        sessions_count = db.query(CampaignSession).filter(CampaignSession.campaign_id == campaign.id).count()
        campaign_response = CampaignResponse.from_orm(campaign)
        campaign_response.sessions_count = sessions_count
        campaign_responses.append(campaign_response)
    
    return {"campaigns": campaign_responses}

@app.get("/campaigns/{campaign_id}")
async def get_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_permission(current_user, "campaigns", "read")
    
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Check if user has access to this campaign
    if current_user.role.name != "admin" and campaign.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    sessions_count = db.query(CampaignSession).filter(CampaignSession.campaign_id == campaign_id).count()
    campaign_response = CampaignResponse.from_orm(campaign)
    campaign_response.sessions_count = sessions_count
    
    return campaign_response

@app.get("/campaigns/{campaign_id}/sessions")
async def get_campaign_sessions(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_permission(current_user, "monitoring", "read")
    
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Check if user has access to this campaign
    if current_user.role.name != "admin" and campaign.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    sessions = db.query(CampaignSession).filter(CampaignSession.campaign_id == campaign_id).all()
    return {"sessions": sessions}

@app.get("/campaigns/{campaign_id}/stats")
async def get_campaign_stats(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_permission(current_user, "monitoring", "read")
    
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Check if user has access to this campaign
    if current_user.role.name != "admin" and campaign.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get statistics
    total_sessions = db.query(CampaignSession).filter(CampaignSession.campaign_id == campaign_id).count()
    active_sessions = db.query(CampaignSession).filter(CampaignSession.campaign_id == campaign_id, CampaignSession.status == "running").count()
    desktop_sessions = db.query(CampaignSession).filter(CampaignSession.campaign_id == campaign_id, CampaignSession.container_type == "desktop").count()
    mobile_sessions = db.query(CampaignSession).filter(CampaignSession.campaign_id == campaign_id, CampaignSession.container_type == "mobile").count()
    
    return {
        "campaign_id": campaign_id,
        "campaign_name": campaign.name,
        "total_sessions": total_sessions,
        "active_sessions": active_sessions,
        "desktop_sessions": desktop_sessions,
        "mobile_sessions": mobile_sessions,
        "browser_type": campaign.browser_type,
        "domain": campaign.domain,
        "status": campaign.status
    }

@app.get("/dashboard/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_permission(current_user, "monitoring", "read")
    
    if current_user.role.name == "admin":
        # Admin sees global stats
        total_campaigns = db.query(Campaign).count()
        total_users = db.query(User).count()
        total_sessions = db.query(CampaignSession).count()
        active_campaigns = db.query(Campaign).filter(Campaign.status == "running").count()
        active_sessions = db.query(CampaignSession).filter(CampaignSession.status == "running").count()
        
        recent_campaigns = db.query(Campaign).order_by(Campaign.created_at.desc()).limit(5).all()
        recent_users = db.query(User).order_by(User.created_at.desc()).limit(5).all()
    else:
        # Regular user sees their own stats
        user_campaigns = db.query(Campaign).filter(Campaign.created_by == current_user.id).all()
        total_campaigns = len(user_campaigns)
        total_sessions = db.query(CampaignSession).join(Campaign).filter(Campaign.created_by == current_user.id).count()
        active_campaigns = len([c for c in user_campaigns if c.status == "running"])
        active_sessions = db.query(CampaignSession).join(Campaign).filter(Campaign.created_by == current_user.id, CampaignSession.status == "running").count()
        
        recent_campaigns = db.query(Campaign).filter(Campaign.created_by == current_user.id).order_by(Campaign.created_at.desc()).limit(5).all()
        recent_users = []  # Users don't see other users
    
    return {
        "total_campaigns": total_campaigns,
        "total_users": total_users if current_user.role.name == "admin" else None,
        "total_sessions": total_sessions,
        "active_campaigns": active_campaigns,
        "active_sessions": active_sessions,
        "recent_campaigns": [{"id": c.id, "name": c.name, "status": c.status, "created_at": c.created_at} for c in recent_campaigns],
        "recent_users": [{"id": u.id, "username": u.username, "created_at": u.created_at} for u in recent_users] if current_user.role.name == "admin" else []
    }

# Helper function to send Telegram notifications
async def send_telegram_notification(chat_id: Optional[str], notification_type: str, title: str, message: str):
    if not chat_id or not telegram_manager.bot:
        return
    
    try:
        full_message = f"🔔 {title}\n\n{message}"
        await telegram_manager.bot.send_message(int(chat_id), full_message)
    except Exception as e:
        print(f"Error sending Telegram notification: {e}")

# Background task for handling Telegram updates
async def telegram_background_task():
    if not telegram_manager.bot:
        return
    
    print("🤖 Telegram bot background task started")
    
    while True:
        try:
            # This would typically poll for updates from Telegram
            # For now, we'll just sleep
            await asyncio.sleep(60)
        except Exception as e:
            print(f"Telegram background task error: {e}")
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    # Initialize roles
    init_roles()
    
    # Start Telegram bot
    await telegram_manager.start()
    
    # Start background task
    asyncio.create_task(telegram_background_task())
    
    print("✅ NoPhish Professional API started")

@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 NoPhish Professional API shutting down")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)