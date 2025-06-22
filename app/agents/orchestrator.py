# ========================================
# app/agents/orchestrator.py - Orquestador Principal
# ========================================

from typing import Dict, Any, Optional
import asyncio
import logging
from datetime import datetime

from .nutrition_agent import NutritionAgent
from .fitness_agent import FitnessAgent
from .research_agent import ResearchAgent
from .personalization_agent import PersonalizationAgent
from ..services.memory_service import MemoryService
from ..services.plan_generator import PlanGenerator

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    def __init__(self):
        self.nutrition_agent = NutritionAgent()
        self.fitness_agent = FitnessAgent()
        self.research_agent = ResearchAgent()
        self.personalization_agent = PersonalizationAgent()
        self.memory_service = MemoryService()
        self.plan_generator = PlanGenerator()
        
        # Keywords para routing
        self.nutrition_keywords = [
            'dieta', 'alimentación', 'comida', 'nutrición', 'calorías', 
            'macros', 'proteína', 'carbohidratos', 'grasas', 'vitaminas'
        ]
        self.fitness_keywords = [
            'ejercicio', 'rutina', 'entrenamiento', 'gimnasio', 'músculo',
            'cardio', 'fuerza', 'peso', 'repeticiones', 'series'
        ]
        self.research_keywords = [
            'estudio', 'investigación', 'científico', 'evidencia', 'pubmed'
        ]

    async def process_message(self, user_id: str, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Procesa un mensaje y lo enruta al agente apropiado"""
        try:
            # Cargar contexto de conversación
            conversation_context = await self.memory_service.get_conversation_context(user_id)
            
            # Cargar perfil de usuario
            user_profile = await self.memory_service.get_user_profile(user_id)
            
            # Determinar el agente apropiado
            agent_type = self._determine_agent(message, conversation_context)
            
            logger.info(f"Enrutando a {agent_type} para usuario {user_id}")
            
            # Procesar con el agente seleccionado
            if agent_type == "nutrition":
                response = await self.nutrition_agent.process(
                    message, user_profile, conversation_context
                )
            elif agent_type == "fitness":
                response = await self.fitness_agent.process(
                    message, user_profile, conversation_context
                )
            elif agent_type == "research":
                response = await self.research_agent.process(
                    message, user_profile, conversation_context
                )
            else:  # personalization
                response = await self.personalization_agent.process(
                    message, user_profile, conversation_context
                )
            
            # Actualizar memoria de conversación
            await self.memory_service.update_conversation(
                user_id, message, response["content"], agent_type
            )
            
            # Generar plan si es necesario
            if response.get("generate_plan"):
                plan = await self.plan_generator.generate_plan(
                    user_id, response["plan_type"], response["plan_data"]
                )
                response["plan"] = plan
            
            return {
                "agent": agent_type,
                "message": response["content"],
                "metadata": response.get("metadata", {}),
                "plan": response.get("plan"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {str(e)}")
            return {
                "agent": "error",
                "message": "Lo siento, ha ocurrido un error procesando tu consulta. Por favor, inténtalo de nuevo.",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def _determine_agent(self, message: str, context: List[Dict]) -> str:
        """Determina qué agente debe procesar el mensaje"""
        message_lower = message.lower()
        
        # Puntuación por keywords
        nutrition_score = sum(1 for keyword in self.nutrition_keywords if keyword in message_lower)
        fitness_score = sum(1 for keyword in self.fitness_keywords if keyword in message_lower)
        research_score = sum(1 for keyword in self.research_keywords if keyword in message_lower)
        
        # Considerar contexto de conversación reciente
        if context:
            last_agent = context[-1].get("agent", "")
            if last_agent and message_lower in ["sí", "si", "continúa", "más"]:
                return last_agent
        
        # Determinar agente basado en puntuación
        if research_score > 0:
            return "research"
        elif nutrition_score > fitness_score:
            return "nutrition"
        elif fitness_score > 0:
            return "fitness"
        else:
            return "personalization"

# ========================================
# app/agents/nutrition_agent.py - Agente de Nutrición
# ========================================

from typing import Dict, Any, List, Optional
import asyncio
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.tools import BaseTool

from ..tools.nutrition_apis import NutritionAPITool, USDAFoodTool, SpoonacularTool
from ..tools.calculators import MacroCalculatorTool, CalorieCalculatorTool

class NutritionAgent:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.3, model="gpt-3.5-turbo")
        
        # Herramientas específicas de nutrición
        self.tools = [
            NutritionAPITool(),
            USDAFoodTool(),
            SpoonacularTool(),
            MacroCalculatorTool(),
            CalorieCalculatorTool()
        ]
        
        # Prompt especializado
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un nutricionista experto y asistente de IA especializado en:
            - Crear planes de alimentación personalizados
            - Calcular macronutrientes y calorías
            - Recomendar alimentos saludables
            - Considerar restricciones dietéticas y alergias
            - Proporcionar información nutricional precisa
            
            Siempre usa información actualizada de las herramientas disponibles.
            Personaliza tus recomendaciones basándote en el perfil del usuario.
            Sé específico con cantidades, porciones y alternativas.
            
            Si necesitas generar un plan de alimentación completo, indica generate_plan=True.
            """),
            ("human", "{input}"),
            ("assistant", "{agent_scratchpad}")
        ])
        
        # Crear agente
        self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        self.executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)

    async def process(self, message: str, user_profile: Dict, context: List[Dict]) -> Dict[str, Any]:
        """Procesa una consulta de nutrición"""
        
        # Preparar contexto del usuario
        user_context = self._prepare_user_context(user_profile, context)
        
        # Crear input completo
        full_input = f"""
        Perfil del usuario: {user_context}
        Consulta: {message}
        """
        
        try:
            # Ejecutar agente
            result = await asyncio.to_thread(
                self.executor.invoke,
                {"input": full_input}
            )
            
            response_content = result["output"]
            
            # Determinar si necesita generar un plan
            generate_plan = any(phrase in message.lower() for phrase in [
                "plan de alimentación", "dieta completa", "menú semanal", 
                "plan nutricional", "qué comer"
            ])
            
            return {
                "content": response_content,
                "generate_plan": generate_plan,
                "plan_type": "nutrition" if generate_plan else None,
                "plan_data": self._extract_plan_data(response_content) if generate_plan else None,
                "metadata": {
                    "tools_used": [tool.name for tool in self.tools],
                    "user_profile_used": bool(user_profile)
                }
            }
            
        except Exception as e:
            return {
                "content": f"Lo siento, ha ocurrido un error procesando tu consulta nutricional: {str(e)}",
                "generate_plan": False,
                "metadata": {"error": str(e)}
            }

    def _prepare_user_context(self, user_profile: Dict, context: List[Dict]) -> str:
        """Prepara el contexto del usuario para el agente"""
        context_parts = []
        
        if user_profile:
            if user_profile.get("age"):
                context_parts.append(f"Edad: {user_profile['age']} años")
            if user_profile.get("weight"):
                context_parts.append(f"Peso: {user_profile['weight']} kg")
            if user_profile.get("height"):
                context_parts.append(f"Altura: {user_profile['height']} cm")
            if user_profile.get("activity_level"):
                context_parts.append(f"Nivel de actividad: {user_profile['activity_level']}")
            if user_profile.get("goals"):
                context_parts.append(f"Objetivos: {user_profile['goals']}")
            if user_profile.get("restrictions"):
                context_parts.append(f"Restricciones dietéticas: {user_profile['restrictions']}")
        
        if context:
            recent_context = context[-3:]  # Últimas 3 interacciones
            context_parts.append("Contexto reciente de la conversación:")
            for ctx in recent_context:
                context_parts.append(f"- {ctx.get('message', '')[:100]}...")
        
        return " | ".join(context_parts) if context_parts else "Sin información de perfil disponible"

    def _extract_plan_data(self, response: str) -> Dict[str, Any]:
        """Extrae datos estructurados para generar un plan"""
        # Lógica simple de extracción - se puede mejorar con NLP
        return {
            "type": "nutrition_plan",
            "duration": "7_days",  # Por defecto semanal
            "content": response
        }