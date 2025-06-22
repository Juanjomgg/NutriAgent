# ========================================
# app/services/memory_service.py - Servicio de Memoria
# ========================================

import redis
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MemoryService:
    def __init__(self):
        # Configuración Redis - usar variables de entorno en producción
        self.redis_client = redis.Redis(
            host='localhost',  # En Render será la URL de Redis
            port=6379,
            db=0,
            decode_responses=True
        )
        
        # TTL por defecto para conversaciones (24 horas)
        self.conversation_ttl = 86400
        # TTL para perfiles de usuario (30 días)
        self.profile_ttl = 2592000

    async def get_conversation_context(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene el contexto de conversación del usuario"""
        try:
            key = f"conversation:{user_id}"
            messages_json = self.redis_client.lrange(key, 0, limit-1)
            
            messages = []
            for msg_json in messages_json:
                try:
                    messages.append(json.loads(msg_json))
                except json.JSONDecodeError:
                    logger.warning(f"Error decodificando mensaje para usuario {user_id}")
                    continue
            
            return messages[::-1]  # Más recientes primero
            
        except Exception as e:
            logger.error(f"Error obteniendo contexto de conversación: {str(e)}")
            return []

    async def update_conversation(self, user_id: str, user_message: str, 
                                agent_response: str, agent_type: str):
        """Actualiza el contexto de conversación"""
        try:
            key = f"conversation:{user_id}"
            
            conversation_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "user_message": user_message,
                "agent_response": agent_response,
                "agent": agent_type
            }
            
            # Agregar al inicio de la lista
            self.redis_client.lpush(key, json.dumps(conversation_entry))
            
            # Mantener solo los últimos 50 mensajes
            self.redis_client.ltrim(key, 0, 49)
            
            # Establecer TTL
            self.redis_client.expire(key, self.conversation_ttl)
            
        except Exception as e:
            logger.error(f"Error actualizando conversación: {str(e)}")

    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Obtiene el perfil del usuario"""
        try:
            key = f"profile:{user_id}"
            profile_json = self.redis_client.get(key)
            
            if profile_json:
                return json.loads(profile_json)
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error obteniendo perfil de usuario: {str(e)}")
            return {}

    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]):
        """Actualiza el perfil del usuario"""
        try:
            key = f"profile:{user_id}"
            
            # Obtener perfil existente
            existing_profile = await self.get_user_profile(user_id)
            
            # Merge con nueva información
            existing_profile.update(profile_data)
            existing_profile["last_updated"] = datetime.utcnow().isoformat()
            
            # Guardar
            self.redis_client.set(key, json.dumps(existing_profile), ex=self.profile_ttl)
            
        except Exception as e:
            logger.error(f"Error actualizando perfil: {str(e)}")

    async def cache_api_response(self, api_key: str, response_data: Any, ttl: int = 3600):
        """Cachea respuestas de APIs externas"""
        try:
            key = f"api_cache:{api_key}"
            self.redis_client.set(key, json.dumps(response_data), ex=ttl)
        except Exception as e:
            logger.error(f"Error cacheando respuesta API: {str(e)}")

    async def get_cached_api_response(self, api_key: str) -> Optional[Any]:
        """Obtiene respuesta cacheada de API"""
        try:
            key = f"api_cache:{api_key}"
            cached_data = self.redis_client.get(key)
            return json.loads(cached_data) if cached_data else None
        except Exception as e:
            logger.error(f"Error obteniendo cache API: {str(e)}")
            return None

    async def close(self):
        """Cierra la conexión Redis"""
        try:
            self.redis_client.close()
        except Exception as e:
            logger.error(f"Error cerrando conexión Redis: {str(e)}")