# ========================================
# app/services/plan_generator.py - Generador de Planes
# ========================================

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json
import logging
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..models.plans import NutritionPlan, WorkoutPlan
from .memory_service import MemoryService

logger = logging.getLogger(__name__)

class PlanGenerator:
    def __init__(self):
        self.memory_service = MemoryService()

    async def generate_plan(self, user_id: str, plan_type: str, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Genera un plan personalizado y lo guarda en BD"""
        try:
            if plan_type == "nutrition":
                return await self._generate_nutrition_plan(user_id, plan_data)
            elif plan_type == "fitness":
                return await self._generate_fitness_plan(user_id, plan_data)
            else:
                raise ValueError(f"Tipo de plan no soportado: {plan_type}")
                
        except Exception as e:
            logger.error(f"Error generando plan: {str(e)}")
            return {"error": str(e)}

    async def _generate_nutrition_plan(self, user_id: str, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Genera plan nutricional detallado"""
        
        # Obtener perfil de usuario para cálculos
        user_profile = await self.memory_service.get_user_profile(user_id)
        
        # Calcular requerimientos calóricos básicos
        calories = self._calculate_daily_calories(user_profile)
        macros = self._calculate_macros(calories, user_profile.get('goals', 'maintenance'))
        
        # Estructura del plan nutricional
        nutrition_plan = {
            "id": f"nutrition_{user_id}_{int(datetime.utcnow().timestamp())}",
            "user_id": user_id,
            "type": "nutrition",
            "duration": plan_data.get("duration", "7_days"),
            "created_at": datetime.utcnow().isoformat(),
            "daily_calories": calories,
            "macros": macros,
            "meals": self._generate_meal_structure(),
            "guidelines": self._generate_nutrition_guidelines(user_profile),
            "shopping_list": self._generate_shopping_list(macros),
            "notes": plan_data.get("content", "")
        }
        
        # Guardar en base de datos
        await self._save_plan_to_db(nutrition_plan)
        
        return nutrition_plan

    async def _generate_fitness_plan(self, user_id: str, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Genera plan de entrenamiento detallado"""
        
        user_profile = await self.memory_service.get_user_profile(user_id)
        
        fitness_plan = {
            "id": f"fitness_{user_id}_{int(datetime.utcnow().timestamp())}",
            "user_id": user_id,
            "type": "fitness",
            "duration": plan_data.get("duration", "4_weeks"),
            "created_at": datetime.utcnow().isoformat(),
            "fitness_level": user_profile.get("fitness_level", "beginner"),
            "weekly_schedule": self._generate_workout_schedule(user_profile),
            "exercises": self._generate_exercise_library(),
            "progression": self._generate_progression_plan(),
            "notes": plan_data.get("content", "")
        }
        
        await self._save_plan_to_db(fitness_plan)
        
        return fitness_plan

    def _calculate_daily_calories(self, user_profile: Dict[str, Any]) -> int:
        """Calcula calorías diarias usando fórmula Harris-Benedict"""
        try:
            age = user_profile.get('age', 30)
            weight = user_profile.get('weight', 70)
            height = user_profile.get('height', 170)
            gender = user_profile.get('gender', 'male')
            activity_level = user_profile.get('activity_level', 'moderate')
            
            # Tasa Metabólica Basal (TMB)
            if gender.lower() == 'female':
                bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
            else:
                bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
            
            # Factor de actividad
            activity_multipliers = {
                'sedentary': 1.2,
                'light': 1.375,
                'moderate': 1.55,
                'active': 1.725,
                'very_active': 1.9
            }
            
            multiplier = activity_multipliers.get(activity_level, 1.55)
            tdee = bmr * multiplier
            
            # Ajustar según objetivos
            goals = user_profile.get('goals', 'maintenance')
            if 'perder peso' in goals.lower() or 'lose weight' in goals.lower():
                return int(tdee * 0.8)  # Déficit del 20%
            elif 'ganar peso' in goals.lower() or 'gain weight' in goals.lower():
                return int(tdee * 1.15)  # Superávit del 15%
            else:
                return int(tdee)  # Mantenimiento
                
        except Exception as e:
            logger.error(f"Error calculando calorías: {str(e)}")
            return 2000  # Valor por defecto

    def _calculate_macros(self, calories: int, goals: str) -> Dict[str, int]:
        """Calcula distribución de macronutrientes"""
        
        if 'ganar músculo' in goals.lower() or 'muscle' in goals.lower():
            # Alto en proteína para ganancia muscular
            protein_ratio = 0.30
            carb_ratio = 0.40
            fat_ratio = 0.30
        elif 'perder peso' in goals.lower() or 'lose weight' in goals.lower():
            # Moderado en proteína, bajo en carbos
            protein_ratio = 0.35
            carb_ratio = 0.30
            fat_ratio = 0.35
        else:
            # Balanceado para mantenimiento
            protein_ratio = 0.25
            carb_ratio = 0.45
            fat_ratio = 0.30
        
        return {
            "protein_g": int((calories * protein_ratio) / 4),
            "carbs_g": int((calories * carb_ratio) / 4),
            "fats_g": int((calories * fat_ratio) / 9),
            "fiber_g": max(25, int(calories / 80))  # Mínimo 25g
        }

    def _generate_meal_structure(self) -> Dict[str, Any]:
        """Genera estructura básica de comidas"""
        return {
            "breakfast": {
                "time": "07:00-09:00",
                "calories_percentage": 25,
                "suggestions": [
                    "Avena con frutas y frutos secos",
                    "Tostadas integrales con aguacate",
                    "Yogur griego con granola"
                ]
            },
            "lunch": {
                "time": "12:00-14:00", 
                "calories_percentage": 35,
                "suggestions": [
                    "Ensalada con proteína (pollo/pescado/legumbres)",
                    "Bowl de quinoa con verduras",
                    "Wrap integral con hummus y vegetales"
                ]
            },
            "snack": {
                "time": "16:00-17:00",
                "calories_percentage": 10,
                "suggestions": [
                    "Frutas con frutos secos",
                    "Yogur natural",
                    "Batido de proteínas"
                ]
            },
            "dinner": {
                "time": "19:00-21:00",
                "calories_percentage": 30,
                "suggestions": [
                    "Pescado con verduras al vapor",
                    "Pollo a la plancha con ensalada",
                    "Legumbres con arroz integral"
                ]
            }
        }

    def _generate_nutrition_guidelines(self, user_profile: Dict[str, Any]) -> List[str]:
        """Genera pautas nutricionales personalizadas"""
        guidelines = [
            "Bebe al menos 2-3 litros de agua al día",
            "Come cada 3-4 horas para mantener el metabolismo activo",
            "Incluye proteína en cada comida principal",
            "Consume al menos 5 porciones de frutas y verduras al día",
            "Limita alimentos procesados y azúcares añadidos"
        ]
        
        # Personalizar según restricciones
        restrictions = user_profile.get('restrictions', '')
        if any(word in restrictions.lower() for word in ['diabetic', 'diabetes']):
            guidelines.append("Controla el índice glucémico de los carbohidratos")
            guidelines.append("Evita azúcares simples y harinas refinadas")
        
        if any(word in restrictions.lower() for word in ['vegetarian', 'vegetariano']):
            guidelines.append("Combina legumbres con cereales para proteína completa")
            guidelines.append("Asegúrate de obtener suficiente B12 y hierro")
        
        return guidelines

    def _generate_shopping_list(self, macros: Dict[str, int]) -> Dict[str, List[str]]:
        """Genera lista de compras básica"""
        return {
            "proteins": [
                "Pollo (pechuga)", "Pescado (salmón, atún)", "Huevos",
                "Legumbres (lentejas, garbanzos)", "Yogur griego"
            ],
            "carbs": [
                "Avena", "Quinoa", "Arroz integral", "Pan integral",
                "Patatas", "Frutas (plátano, manzana, bayas)"
            ],
            "fats": [
                "Aguacate", "Frutos secos", "Aceite de oliva",
                "Semillas (chía, lino)", "Pescado graso"
            ],
            "vegetables": [
                "Espinacas", "Brócoli", "Tomates", "Pepino",
                "Pimientos", "Cebolla", "Ajo"
            ],
            "others": [
                "Especias variadas", "Limón", "Vinagre",
                "Té verde", "Agua con gas"
            ]
        }

    def _generate_workout_schedule(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Genera horario semanal de entrenamientos"""
        fitness_level = user_profile.get('fitness_level', 'beginner')
        
        if fitness_level == 'beginner':
            return {
                "monday": {"type": "full_body", "duration": 45, "intensity": "moderate"},
                "tuesday": {"type": "rest", "activity": "caminar 30min"},
                "wednesday": {"type": "full_body", "duration": 45, "intensity": "moderate"},
                "thursday": {"type": "rest", "activity": "yoga o stretching"},
                "friday": {"type": "full_body", "duration": 45, "intensity": "moderate"},
                "saturday": {"type": "cardio", "duration": 30, "intensity": "light"},
                "sunday": {"type": "rest", "activity": "descanso completo"}
            }
        elif fitness_level == 'intermediate':
            return {
                "monday": {"type": "upper_body", "duration": 60, "intensity": "moderate"},
                "tuesday": {"type": "lower_body", "duration": 60, "intensity": "moderate"},
                "wednesday": {"type": "cardio", "duration": 30, "intensity": "moderate"},
                "thursday": {"type": "upper_body", "duration": 60, "intensity": "high"},
                "friday": {"type": "lower_body", "duration": 60, "intensity": "high"},
                "saturday": {"type": "full_body", "duration": 45, "intensity": "light"},
                "sunday": {"type": "rest", "activity": "stretching"}
            }
        else:  # advanced
            return {
                "monday": {"type": "push", "duration": 75, "intensity": "high"},
                "tuesday": {"type": "pull", "duration": 75, "intensity": "high"},
                "wednesday": {"type": "legs", "duration": 90, "intensity": "high"},
                "thursday": {"type": "push", "duration": 75, "intensity": "moderate"},
                "friday": {"type": "pull", "duration": 75, "intensity": "moderate"},
                "saturday": {"type": "legs", "duration": 90, "intensity": "moderate"},
                "sunday": {"type": "rest", "activity": "yoga o movilidad"}
            }

    def _generate_exercise_library(self) -> Dict[str, List[Dict[str, Any]]]:
        """Genera biblioteca de ejercicios"""
        return {
            "upper_body": [
                {"name": "Push-ups", "sets": "3", "reps": "8-15", "muscle": "chest, triceps"},
                {"name": "Pull-ups", "sets": "3", "reps": "5-12", "muscle": "back, biceps"},
                {"name": "Shoulder Press", "sets": "3", "reps": "10-15", "muscle": "shoulders"},
                {"name": "Rows", "sets": "3", "reps": "10-15", "muscle": "back"}
            ],
            "lower_body": [
                {"name": "Squats", "sets": "3", "reps": "12-20", "muscle": "quads, glutes"},
                {"name": "Deadlifts", "sets": "3", "reps": "8-12", "muscle": "hamstrings, glutes"},
                {"name": "Lunges", "sets": "3", "reps": "10-15 each leg", "muscle": "legs, glutes"},
                {"name": "Calf Raises", "sets": "3", "reps": "15-25", "muscle": "calves"}
            ],
            "cardio": [
                {"name": "Running", "duration": "20-45min", "intensity": "moderate"},
                {"name": "Cycling", "duration": "30-60min", "intensity": "moderate"},
                {"name": "Swimming", "duration": "20-40min", "intensity": "moderate"},
                {"name": "HIIT", "duration": "15-25min", "intensity": "high"}
            ]
        }

    def _generate_progression_plan(self) -> Dict[str, str]:
        """Genera plan de progresión"""
        return {
            "week_1": "Enfócate en la técnica correcta, usa pesos ligeros",
            "week_2": "Aumenta ligeramente el peso o las repeticiones",
            "week_3": "Incrementa intensidad, mantén buena forma",
            "week_4": "Deload week - reduce intensidad para recuperación",
            "general": "Aumenta peso/reps cuando puedas completar todas las series cómodamente"
        }

    async def _save_plan_to_db(self, plan_data: Dict[str, Any]):
        """Guarda el plan en la base de datos"""
        try:
            # Aquí se implementaría la lógica de guardado en PostgreSQL
            # Por ahora lo guardamos en cache Redis como backup
            cache_key = f"plan:{plan_data['id']}"
            await self.memory_service.redis_client.set(
                cache_key, 
                json.dumps(plan_data), 
                ex=2592000  # 30 días
            )
            logger.info(f"Plan guardado: {plan_data['id']}")
            
        except Exception as e:
            logger.error(f"Error guardando plan: {str(e)}")