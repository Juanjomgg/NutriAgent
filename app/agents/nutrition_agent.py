# ========================================
# app/agents/nutrition_agent.py - Agente de Nutrición
# ========================================

from typing import Dict, Any, List, Optional
import asyncio
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.tools import BaseTool
from ..tools.nutrition_apis import EdamamMealPlannerTool
from ..tools.calculators import MacroCalculatorTool, CalorieCalculatorTool

class NutritionAgent:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.3, model="gpt-3.5-turbo")
        
        # Herramientas específicas de nutrición
        self.tools = [
            EdamamMealPlannerTool(),
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