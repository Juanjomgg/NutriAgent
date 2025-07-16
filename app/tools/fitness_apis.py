# Herramientas de integración con APIs de fitness
import httpx
from typing import Dict, Any
import logging
import os
from dotenv import load_dotenv

load_dotenv()

API_EXERCICEDB = os.getenv('API_EXERCICEDB_KEY')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExerciseDBTool:
    """
    Herramienta para integración con ExerciseDB API
    Proporciona acceso a una amplia base de datos de ejercicios con imágenes y descripciones
    """
    
    def __init__(self):
        """
        Inicializa la herramienta ExerciseDB
        
        Args:
            api_key: Clave API de RapidAPI para ExerciseDB (requerida)
        """
        self.base_url = "https://exercisedb.p.rapidapi.com"
        self.api_key = API_EXERCICEDB  # Cargar desde variable de entorno
        self.headers = {
            "X-RapidAPI-Key": self.api_key or "TU_API_KEY_AQUI",
            "X-RapidAPI-Host": "exercisedb.p.rapidapi.com"
        }
        self.exercises_list = {}
        self.timeout = 30.0
    
    async def run(self, **kwargs) -> Dict[str, Any]:
        """
        Ejecuta una acción específica con la API de ExerciseDB
        
        Args:
            action: Acción a realizar (get_by_target, get_target_list)
            **kwargs: Parámetros adicionales según la acción
        
        Returns:
            Dict con los resultados de la API
        """
        try:
            action = kwargs.get('action')
            if action == "get_by_target":
                return await self.get_exercises_by_target(kwargs.get('target'))
            elif action == "get_target_list":
                return await self.get_target_list(kwargs.get('limit'))
            else:
                raise ValueError(f"Acción no reconocida: {action}")
        except Exception as e:
            logger.error(f"Error en ExerciseDBTool: {e}")
            return {"error": str(e)}

    
    async def get_exercises_by_target(self, target: str) -> Dict[str, Any]:
        """Obtiene ejercicios por músculo objetivo"""
        try:

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                try:
                    url = f"{self.base_url}/exercises/target/{target}"
                    response = await client.get(url, headers=self.headers)
                
                    if response.status_code == 200:
                        exercises = response.json()
                        for exercise in exercises:
                            data = {
                                "id": exercise["id"],
                                "name": exercise["name"],
                                "difficulty": exercise["difficulty"],
                            }
                            self.exercises_list.update(data)
                    
                        return {
                            "success": True,
                            "data": self.exercises_list,
                        }
                    else:
                        raise httpx.HTTPException(
                            status_code=response.status_code,
                            detail=f"Error en ExerciseDB API: {response.status_code}"
                        )
                except httpx.TimeoutException:
                    raise Exception("Request timeout")
                except httpx.RequestError as e:
                    raise Exception(f"Error de conexión: {str(e)}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Error al obtener ejercicios por objetivo: {e}")
            raise Exception(f"Error: {e.response.status_code} - {e.response.text}")


    async def get_target_list(self, limit: str) -> Dict[str, Any]:
        """Obtiene lista de músculos objetivo disponibles"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/exercises/targetList"
                response = await client.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    targets = response.json()
                    return {
                        "success": True,
                        "data": targets [:limit] if limit else targets,
                        "count": len(targets)
                    }
                else:
                    raise Exception(f"Error en ExerciseDB API: {response.status_code}"
                    )
            except httpx.TimeoutException:
                raise Exception("Timeout en la API de ExerciseDB")
            except httpx.HTTPStatusError as e:
                logger.error(f"Error al obtener lista de objetivos: {e}")
                raise Exception(f"Error de conexión: {str(e)}")

