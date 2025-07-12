# Herramientas de integración con APIs de fitness
import httpx
import asyncio
import json
from typing import Dict, List, Optional, Any
import logging
from fastapi import HTTPException
import sys
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
        self.timeout = 30.0
    
    async def run(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Ejecuta una acción específica con la API de ExerciseDB
        
        Args:
            action: Acción a realizar ('get_exercises', 'get_by_bodypart', 'get_by_equipment', etc.)
            **kwargs: Parámetros adicionales según la acción
        
        Returns:
            Dict con los resultados de la API
        """
        try:
            if action == "get_by_target":
                return await self.get_exercises_by_target(kwargs.get('target'))
            elif action == "get_target_list":
                return await self.get_target_list()
            else:
                if 'fastapi' in sys.modules:
                    raise HTTPException(status_code=400, detail=f"Acción no reconocida: {action}")
                else:
                    raise ValueError(f"Acción no reconocida: {action}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error en ExerciseDBTool: {e}")
            if 'fastapi' in sys.modules:
                raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
            else:
                return {"error": str(e)}

    
    async def get_exercises_by_target(self, target: str) -> Dict[str, Any]:
        """Obtiene ejercicios por músculo objetivo"""
        if not target:
            raise HTTPException(status_code=400, detail="Target es requerido")
            
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
                        exercise_list.update(data)
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Error en ExerciseDB API: {response.status_code}"
                    )
            except httpx.TimeoutException:
                raise HTTPException(status_code=408, detail="Timeout en la API de ExerciseDB")
            except httpx.RequestError as e:
                raise HTTPException(status_code=503, detail=f"Error de conexión: {str(e)}")
    
    
    async def get_target_list(self) -> Dict[str, Any]:
        """Obtiene lista de músculos objetivo disponibles"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                url = f"{self.base_url}/exercises/targetList"
                response = await client.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    targets = response.json()
                    return {
                        "success": True,
                        "data": targets,
                        "count": len(targets)
                    }
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Error en ExerciseDB API: {response.status_code}"
                    )
            except httpx.TimeoutException:
                raise HTTPException(status_code=408, detail="Timeout en la API de ExerciseDB")
            except httpx.RequestError as e:
                raise HTTPException(status_code=503, detail=f"Error de conexión: {str(e)}")

