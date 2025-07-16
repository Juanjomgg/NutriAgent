# ========================================
# app/agents/orchestrator.py - Orquestador Principal
# ========================================

from typing import Dict, Any, Optional, List
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