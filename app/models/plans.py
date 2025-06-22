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

# ========================================
# app/tools/nutrition_apis.py - Herramientas de APIs de Nutrición
# ========================================

import httpx
import asyncio
from typing import Dict, Any, List, Optional
from langchain.tools import BaseTool
from pydantic import BaseModel
import os
import logging

logger = logging.getLogger(__name__)

class NutritionAPITool(BaseTool):
    name = "nutrition_search"
    description = "Busca información nutricional de alimentos usando múltiples APIs"
    
    async def _arun(self, food_name: str) -> Dict[str, Any]:
        """Busca información nutricional de un alimento"""
        try:
            # Intentar con USDA primero (gratuita)
            usda_result = await self._search_usda(food_name)
            if usda_result:
                return usda_result
            
            # Fallback a Edamam si USDA no devuelve resultados
            edamam_result = await self._search_edamam(food_name)
            return edamam_result if edamam_result else {"error": "No se encontró información"}
            
        except Exception as e:
            logger.error(f"Error en búsqueda nutricional: {str(e)}")
            return {"error": str(e)}

    def _run(self, food_name: str) -> Dict[str, Any]:
        """Versión síncrona"""
        return asyncio.run(self._arun(food_name))

    async def _search_usda(self, food_name: str) -> Optional[Dict[str, Any]]:
        """Busca en USDA FoodData Central API (gratuita)"""
        try:
            api_key = os.getenv("USDA_API_KEY", "DEMO_KEY")  # Obtener key gratuita
            url = "https://api.nal.usda.gov/fdc/v1/foods/search"
            
            params = {
                "query": food_name,
                "dataType": ["Foundation", "SR Legacy"],
                "pageSize": 5,
                "api_key": api_key
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                foods = data.get("foods", [])
                
                if foods:
                    food = foods[0]  # Tomar el primer resultado
                    return self._format_usda_response(food)
                    
                return None
                
        except Exception as e:
            logger.error(f"Error USDA API: {str(e)}")
            return None

    async def _search_edamam(self, food_name: str) -> Optional[Dict[str, Any]]:
        """Busca en Edamam Food Database API"""
        try:
            app_id = os.getenv("EDAMAM_FOOD_APP_ID")
            app_key = os.getenv("EDAMAM_FOOD_APP_KEY")
            
            if not app_id or not app_key:
                logger.warning("Credenciales de Edamam no configuradas")
                return None
            
            url = "https://api.edamam.com/api/food-database/v2/parser"
            
            params = {
                "app_id": app_id,
                "app_key": app_key,
                "ingr": food_name,
                "nutrition-type": "cooking"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                foods = data.get("parsed", [])
                
                if foods:
                    food = foods[0]["food"]
                    return self._format_edamam_response(food)
                    
                return None
                
        except Exception as e:
            logger.error(f"Error Edamam API: {str(e)}")
            return None

    def _format_usda_response(self, food_data: Dict) -> Dict[str, Any]:
        """Formatea respuesta de USDA"""
        nutrients = {}
        for nutrient in food_data.get("foodNutrients", []):
            name = nutrient.get("nutrientName", "").lower()
            value = nutrient.get("value", 0)
            unit = nutrient.get("unitName", "")
            
            if "protein" in name:
                nutrients["protein"] = f"{value} {unit}"
            elif "carbohydrate" in name:
                nutrients["carbs"] = f"{value} {unit}"
            elif "fat" in name and "fatty" not in name:
                nutrients["fat"] = f"{value} {unit}"
            elif "energy" in name or "calorie" in name:
                nutrients["calories"] = f"{value} {unit}"
            elif "fiber" in name:
                nutrients["fiber"] = f"{value} {unit}"
        
        return {
            "food_name": food_data.get("description", ""),
            "brand": food_data.get("brandOwner", ""),
            "nutrients": nutrients,
            "serving_size": "100g",
            "source": "USDA"
        }

    def _format_edamam_response(self, food_data: Dict) -> Dict[str, Any]:
        """Formatea respuesta de Edamam"""
        nutrients = food_data.get("nutrients", {})
        
        return {
            "food_name": food_data.get("label", ""),
            "brand": food_data.get("brand", ""),
            "nutrients": {
                "calories": f"{nutrients.get('ENERC_KCAL', 0)} kcal",
                "protein": f"{nutrients.get('PROCNT', 0)} g",
                "carbs": f"{nutrients.get('CHOCDF', 0)} g",
                "fat": f"{nutrients.get('FAT', 0)} g",
                "fiber": f"{nutrients.get('FIBTG', 0)} g"
            },
            "serving_size": "100g",
            "source": "Edamam"
        }

class USDAFoodTool(BaseTool):
    name = "usda_food_search"
    description = "Busca alimentos específicamente en la base de datos USDA (gratuita)"
    
    async def _arun(self, food_query: str) -> str:
        """Búsqueda específica en USDA"""
        nutrition_tool = NutritionAPITool()
        result = await nutrition_tool._search_usda(food_query)
        
        if result:
            return f"Información nutricional de {result['food_name']}: {result['nutrients']}"
        else:
            return f"No se encontró información para {food_query} en USDA"

    def _run(self, food_query: str) -> str:
        return asyncio.run(self._arun(food_query))

class SpoonacularTool(BaseTool):
    name = "recipe_search"
    description = "Busca recetas saludables y su información nutricional"
    
    async def _arun(self, recipe_query: str) -> Dict[str, Any]:
        """Busca recetas en Spoonacular API"""
        try:
            api_key = os.getenv("SPOONACULAR_API_KEY")
            if not api_key:
                return {"error": "API key de Spoonacular no configurada"}
            
            url = "https://api.spoonacular.com/recipes/