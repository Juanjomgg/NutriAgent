# ========================================
# app/models/user.py - Modelo de Usuario
# ========================================

from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from sqlalchemy.sql import func
from ..database.connection import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    age = Column(Integer)
    weight = Column(Integer)  # en kg
    height = Column(Integer)  # en cm
    gender = Column(String)
    activity_level = Column(String)  # sedentary, light, moderate, active, very_active
    fitness_level = Column(String)   # beginner, intermediate, advanced
    goals = Column(Text)
    restrictions = Column(Text)      # alergias, restricciones dietéticas
    injuries = Column(Text)          # lesiones o limitaciones físicas
    equipment = Column(Text)         # equipo disponible
    time_available = Column(String)  # tiempo disponible para entrenar
    profile_data = Column(JSON)      # datos adicionales en JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# ========================================
# app/models/conversation.py - Modelo de Conversaciones
# ========================================

from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from sqlalchemy.sql import func
from ..database.connection import Base

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    session_id = Column(String, index=True)
    messages = Column(JSON)  # Array de mensajes de la conversación
    agent_type = Column(String)  # nutrition, fitness, research, personalization
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())