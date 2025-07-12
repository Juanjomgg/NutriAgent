# ========================================
# app/models/plans.py - Modelos de Planes
# ========================================

from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Float
from sqlalchemy.sql import func
from ..database.connection import Base

class NutritionPlan(Base):
    __tablename__ = "nutrition_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    plan_id = Column(String, unique=True, index=True)  # ID único del plan
    name = Column(String)
    duration = Column(String)  # 7_days, 14_days, 30_days
    daily_calories = Column(Integer)
    protein_g = Column(Integer)
    carbs_g = Column(Integer)
    fats_g = Column(Integer)
    fiber_g = Column(Integer)
    plan_data = Column(JSON)  # Estructura completa del plan
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class WorkoutPlan(Base):
    __tablename__ = "workout_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    plan_id = Column(String, unique=True, index=True)
    name = Column(String)
    duration = Column(String)  # 4_weeks, 8_weeks, 12_weeks
    fitness_level = Column(String)
    weekly_frequency = Column(Integer)  # días por semana
    plan_data = Column(JSON)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
