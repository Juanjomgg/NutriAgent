# ========================================
# app/agents/personalization_agent.py - Agente de Personalización
# ========================================

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

class PersonalizationAgent:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.4, model="gpt-3.5-turbo")
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un asistente especializado en recopilar información personal 
            para crear perfiles de usuarios de nutrición y fitness.
            
            Tu trabajo es:
            - Hacer preguntas relevantes para entender objetivos del usuario
            - Recopilar información sobre estilo de vida, preferencias y limitaciones
            - Crear perfiles personalizados basados en las respuestas
            - Guiar a usuarios nuevos a través del proceso de configuración
            - Actualizar perfiles existentes con nueva información
            
            Sé amigable, profesional y haz preguntas específicas una a la vez.
            Explica por qué necesitas cierta información.
            """),
            ("human", "{input}"),
            ("assistant", "")
        ])

    async def process(self, message: str, user_profile: Dict, context: List[Dict]) -> Dict[str, Any]:
        """Procesa consultas de personalización y configuración de perfil"""
        
        # Determinar si es usuario nuevo o existente
        is_new_user = not user_profile or len(user_profile) == 0
        
        if is_new_user:
            response = await self._handle_new_user(message)
        else:
            response = await self._handle_existing_user(message, user_profile, context)
        
        return {
            "content": response,
            "generate_plan": False,
            "metadata": {
                "profile_update_needed": self._needs_profile_update(message),
                "new_user": is_new_user
            }
        }

    async def _handle_new_user(self, message: str) -> str:
        """Maneja usuarios nuevos"""
        welcome_questions = [
            "¡Hola! Soy tu asistente de nutrición y fitness. Para poder ayudarte mejor, me gustaría conocerte un poco.",
            "¿Cuál es tu objetivo principal? (perder peso, ganar músculo, mejorar salud general, etc.)",
            "¿Cuántos años tienes y cuál es tu nivel de actividad física actual?",
            "¿Tienes alguna restricción alimentaria, alergia o condición médica que deba considerar?"
        ]
        
        return "\n\n".join(welcome_questions)

    async def _handle_existing_user(self, message: str, user_profile: Dict, context: List[Dict]) -> str:
        """Maneja usuarios existentes"""
        
        full_input = f"""
        Información del usuario:
        - Objetivos: {user_profile.get('goals', 'No especificados')}
        - Edad: {user_profile.get('age', 'No especificada')}
        - Nivel de actividad: {user_profile.get('activity_level', 'No especificado')}
        - Restricciones: {user_profile.get('restrictions', 'Ninguna')}
        
        Mensaje del usuario: {message}
        
        Responde de manera personalizada y útil. Si el usuario quiere actualizar su información,
        haz preguntas específicas para obtener los datos necesarios.
        """
        
        try:
            response = await self.llm.ainvoke(self.prompt.format_messages(input=full_input))
            return response.content
        except Exception as e:
            return f"Hola! ¿En qué puedo ayudarte hoy con tu nutrición y fitness? (Error: {str(e)})"

    def _needs_profile_update(self, message: str) -> bool:
        """Determina si el mensaje requiere actualización de perfil"""
        update_keywords = [
            "cambié", "actualizar", "modificar", "nuevo objetivo", 
            "ahora peso", "mi edad", "restricción", "alergia"
        ]
        return any(keyword in message.lower() for keyword in update_keywords)