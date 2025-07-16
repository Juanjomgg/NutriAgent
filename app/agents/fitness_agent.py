# ========================================
# app/agents/fitness_agent.py - Agente de Fitness
# ========================================

from typing import Dict, Any, List
import asyncio
import re
from langchain.agents import AgentExecutor, create_openapi_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from ..tools.fitness_apis import ExerciseDBTool
from ..tools.calculators import WorkoutCalculatorTool, CalorieCalculatorTool, MacroCalculatorTool

class FitnessAgent:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.3, model="gpt-3.5-turbo")
        
        self.tools = [
            ExerciseDBTool(),
            WorkoutCalculatorTool(),
            CalorieCalculatorTool(),
            MacroCalculatorTool()
        ]
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un entrenador personal experto especializado en crear rutinas personalizadas, 
            recomendar ejercicios específicos, calcular necesidades calóricas y distribuir macronutrientes.
            
            HERRAMIENTAS DISPONIBLES Y CUÁNDO USARLAS:
            
            🏋️ ExerciseDBTool - USA CUANDO:
            - Usuario pregunta por ejercicios específicos para un músculo
            - Necesita variedad de ejercicios para un grupo muscular
            - Quiere alternativas a ejercicios básicos
            - Menciona músculos específicos (pecho, espalda, brazos, piernas, etc.)
            - Pide ejercicios con equipo específico
            
            Acciones disponibles:
            • "get_by_target": Obtiene ejercicios por músculo objetivo
              Parámetro: target (ej: "biceps", "chest", "quads", "lats")
            • "get_target_list": Lista todos los músculos disponibles
            
            Músculos objetivo principales:
            - Pecho: "pectorals", "chest"
            - Espalda: "lats", "traps", "rhomboids"  
            - Hombros: "delts", "shoulders"
            - Brazos: "biceps", "triceps", "forearms"
            - Piernas: "quads", "hamstrings", "calves", "glutes"
            - Core: "abs", "obliques"
            
            📊 WorkoutCalculatorTool - USA CUANDO:
            - Usuario pide una rutina semanal básica
            - Necesita estructura general de entrenamiento
            - Pregunta por división de días/grupos musculares
            - Quiere saber frecuencia según su nivel
            
            Parámetros: nivel ("principiante", "intermedio", "avanzado")
                       objetivo ("fuerza", "hipertrofia", "resistencia")
            
            🔥 CalorieCalculatorTool - USA CUANDO:
            - Usuario pregunta cuántas calorías necesita
            - Quiere calcular su metabolismo basal
            - Menciona pérdida/ganancia de peso
            - Pregunta sobre déficit/superávit calórico
            
            Parámetros: sexo, edad, peso (kg), altura (cm), actividad
            Niveles: "sedentario", "ligero", "moderado", "activo", "muy activo"
            
            🥗 MacroCalculatorTool - USA CUANDO:
            - Usuario pregunta sobre distribución de macronutrientes
            - Quiere saber gramos de proteína/carbos/grasas
            - Menciona dieta específica (alta proteína, low carb, etc.)
            - Pregunta sobre nutrición para su objetivo
            
            Parámetros: calorias, proteina_pct, grasa_pct, carb_pct
            
            DECISIONES INTELIGENTES:
            ✅ USA ExerciseDB cuando mencionen músculos específicos o ejercicios
            ✅ USA WorkoutCalculator para rutinas generales o principiantes
            ✅ USA CalorieCalculator si dan datos físicos o mencionan peso
            ✅ USA MacroCalculator después de calcular calorías o si preguntan nutrición
            ✅ Combina herramientas cuando sea necesario (ej: calorías + macros)
            
            ❌ NO uses ExerciseDB para preguntas generales sobre fitness
            ❌ NO uses calculadoras sin datos suficientes del usuario
            ❌ NO uses WorkoutCalculator si piden ejercicios específicos
            
            FLUJO RECOMENDADO:
            1. Analiza la consulta específica del usuario
            2. Identifica qué información necesitas
            3. Usa las herramientas apropiadas en orden lógico
            4. Combina resultados para respuesta completa
            5. Personaliza según perfil del usuario
            
            Siempre considera seguridad, progresión gradual y limitaciones físicas.
            Para rutinas completas con múltiples días, indica generate_plan=True.
            """),
            ("human", "{input}"),
            ("assistant", "{agent_scratchpad}")
        ])
        
        self.agent = create_openapi_agent(self.llm, self.tools, self.prompt)
        self.executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)

    async def process(self, message: str, user_profile: Dict, context: List[Dict]) -> Dict[str, Any]:
        """Procesa una consulta de fitness"""
        
        user_context = self._prepare_user_context(user_profile, context)
        
        full_input = f"""
        Perfil del usuario: {user_context}
        Consulta: {message}
        """
        
        try:
            result = await asyncio.to_thread(
                self.executor.invoke,
                {"input": full_input}
            )
            
            response_content = result["output"]
            
            # Detectar si se necesita generar un plan
            generate_plan = self._should_generate_plan(message, response_content)
            
            # Extraer información de herramientas utilizadas
            tools_used = self._extract_tools_used(result)
            
            return {
                "content": response_content,
                "generate_plan": generate_plan,
                "plan_type": "fitness" if generate_plan else None,
                "plan_data": self._extract_plan_data(response_content, message) if generate_plan else None,
                "metadata": {
                    "tools_used": tools_used,
                    "user_profile_used": bool(user_profile),
                    "context_items": len(context) if context else 0
                }
            }
            
        except Exception as e:
            return {
                "content": f"Lo siento, ha ocurrido un error procesando tu consulta de fitness: {str(e)}",
                "generate_plan": False,
                "metadata": {"error": str(e)}
            }

    def _prepare_user_context(self, user_profile: Dict, context: List[Dict]) -> str:
        """Prepara contexto específico para fitness"""
        context_parts = []
        
        if user_profile:
            # Información básica del usuario
            if user_profile.get("age"):
                context_parts.append(f"Edad: {user_profile['age']}")
            if user_profile.get("gender"):
                context_parts.append(f"Sexo: {user_profile['gender']}")
            if user_profile.get("weight"):
                context_parts.append(f"Peso: {user_profile['weight']} kg")
            if user_profile.get("height"):
                context_parts.append(f"Altura: {user_profile['height']} cm")
            
            # Información específica de fitness
            if user_profile.get("fitness_level"):
                context_parts.append(f"Nivel fitness: {user_profile['fitness_level']}")
            if user_profile.get("goals"):
                context_parts.append(f"Objetivos: {user_profile['goals']}")
            if user_profile.get("injuries"):
                context_parts.append(f"Lesiones/limitaciones: {user_profile['injuries']}")
            if user_profile.get("equipment"):
                context_parts.append(f"Equipo disponible: {user_profile['equipment']}")
            if user_profile.get("time_available"):
                context_parts.append(f"Tiempo disponible: {user_profile['time_available']}")
            if user_profile.get("activity_level"):
                context_parts.append(f"Nivel actividad: {user_profile['activity_level']}")
        
        # Agregar contexto de conversaciones previas
        if context:
            recent_context = [item.get("content", "") for item in context[-3:]]  # Últimas 3 interacciones
            if recent_context:
                context_parts.append(f"Contexto previo: {' | '.join(recent_context)}")
        
        return " | ".join(context_parts) if context_parts else "Sin información específica de fitness"

    def _should_generate_plan(self, message: str, response: str) -> bool:
        """Determina si se debe generar un plan de entrenamiento"""
        plan_keywords = [
            "rutina", "plan de entrenamiento", "ejercicios para", 
            "programa de", "workout", "entrenamiento", "planificar",
            "semana", "mes", "horario", "cronograma"
        ]
        
        message_lower = message.lower()
        response_lower = response.lower()
        
        # Buscar palabras clave en el mensaje del usuario
        has_plan_keywords = any(keyword in message_lower for keyword in plan_keywords)
        
        # Buscar indicadores en la respuesta
        has_structured_response = any(indicator in response_lower for indicator in [
            "día 1", "lunes", "martes", "semana", "rutina", "programa"
        ])
        
        return has_plan_keywords or has_structured_response

    def _extract_tools_used(self, result: Dict) -> List[str]:
        """Extrae las herramientas utilizadas del resultado"""
        tools_used = []
        
        # Intentar extraer de diferentes partes del resultado
        if "intermediate_steps" in result:
            for step in result["intermediate_steps"]:
                if hasattr(step, "tool"):
                    tools_used.append(step.tool)
        
        # Nombres de herramientas disponibles
        available_tools = [
            "ExerciseDBTool", "WorkoutCalculatorTool", 
            "CalorieCalculatorTool", "MacroCalculatorTool"
        ]
        
        # Si no se pudo extraer, intentar detectar por contenido
        if not tools_used:
            response_content = result.get("output", "").lower()
            if "ejercicio" in response_content or "target" in response_content:
                tools_used.append("ExerciseDBTool")
            if "rutina" in response_content or "entrenamiento" in response_content:
                tools_used.append("WorkoutCalculatorTool")
            if "caloría" in response_content or "tmb" in response_content:
                tools_used.append("CalorieCalculatorTool")
            if "macro" in response_content or "proteína" in response_content:
                tools_used.append("MacroCalculatorTool")
        
        return tools_used

    def _extract_plan_data(self, response: str, original_message: str) -> Dict[str, Any]:
        """Extrae datos para generar plan de entrenamiento"""
        
        # Determinar el tipo de plan basado en el contenido
        plan_type = "fitness_plan"
        duration = "4_weeks"  # Por defecto
        
        # Detectar duración específica
        if "semana" in original_message.lower():
            duration = "1_week"
        elif "mes" in original_message.lower():
            duration = "4_weeks"
        elif "día" in original_message.lower():
            duration = "1_day"
        
        # Detectar tipo específico de plan
        if "fuerza" in original_message.lower():
            plan_type = "strength_plan"
        elif "hipertrofia" in original_message.lower() or "músculo" in original_message.lower():
            plan_type = "hypertrophy_plan"
        elif "resistencia" in original_message.lower() or "cardio" in original_message.lower():
            plan_type = "endurance_plan"
        elif "pérdida" in original_message.lower() or "adelgazar" in original_message.lower():
            plan_type = "weight_loss_plan"
        
        # Extraer ejercicios mencionados
        exercises = self._extract_exercises_from_response(response)
        
        return {
            "type": plan_type,
            "duration": duration,
            "content": response,
            "exercises": exercises,
            "created_from": "fitness_agent",
            "original_query": original_message
        }
    
    def _extract_exercises_from_response(self, response: str) -> List[str]:
        """Extrae nombres de ejercicios de la respuesta"""
        exercises = []
        
        # Patrones comunes para ejercicios
        exercise_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[a-z]+)*)\s+(?:con|de|en)',
            r'\b(Press|Curl|Row|Squat|Deadlift|Pull|Push)[a-z\s]*',
            r'\b([A-Z][a-z]+)\s+(?:bíceps|tríceps|pecho|espalda|piernas)'
        ]
        
        for pattern in exercise_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            exercises.extend(matches)
        
        # Eliminar duplicados y mantener orden
        seen = set()
        unique_exercises = []
        for exercise in exercises:
            if exercise.lower() not in seen:
                seen.add(exercise.lower())
                unique_exercises.append(exercise)
        
        return unique_exercises[:10]  # Limitar a 10 ejercicios principales