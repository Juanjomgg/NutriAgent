# ========================================
# app/agents/fitness_agent.py - Agente de Fitness
# ========================================

from typing import Dict, Any, List
import asyncio
from langchain.agents import AgentExecutor, create_openapi_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from ..tools.fitness_apis import ExerciseDBTool
from ..tools.calculators import WorkoutCalculatorTool

class FitnessAgent:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.3, model="gpt-3.5-turbo")
        
        self.tools = [
            ExerciseDBTool(),
            WorkoutCalculatorTool()
        ]
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un entrenador personal experto especializado en:
            - Crear rutinas de entrenamiento personalizadas
            - Recomendar ejercicios apropiados según nivel y objetivos
            - Calcular volumen de entrenamiento y progresiones
            - Considerar limitaciones físicas y preferencias
            - Proporcionar técnica y seguridad en ejercicios
            
            Usa las herramientas disponibles para obtener información actualizada.
            Personaliza según experiencia, objetivos y limitaciones del usuario.
            Incluye calentamiento, ejercicios principales y enfriamiento.
            
            Si necesitas crear una rutina completa, indica generate_plan=True.
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
            
            generate_plan = any(phrase in message.lower() for phrase in [
                "rutina", "plan de entrenamiento", "ejercicios para", 
                "programa de", "workout"
            ])
            
            return {
                "content": response_content,
                "generate_plan": generate_plan,
                "plan_type": "fitness" if generate_plan else None,
                "plan_data": self._extract_plan_data(response_content) if generate_plan else None,
                "metadata": {
                    "tools_used": [tool.name for tool in self.tools],
                    "user_profile_used": bool(user_profile)
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
        
        return " | ".join(context_parts) if context_parts else "Sin información específica de fitness"

    def _extract_plan_data(self, response: str) -> Dict[str, Any]:
        """Extrae datos para generar plan de entrenamiento"""
        return {
            "type": "fitness_plan",
            "duration": "4_weeks",
            "content": response
        }