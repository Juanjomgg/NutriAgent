# Herramientas de integración con APIs de nutrición
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv('API_URL')
APP_ID = os.getenv('APP_ID')
API_KEY = os.getenv('API_KEY')

class EdamamMealPlannerTool:
    name = "EdamamMealPlannerTool"


    def run(self, params: dict):
        """
        Crea un plan de comidas usando la API Meal Planner de Edamam.
        Espera un diccionario params con la estructura compatible con la API Edamam.
        """
        # Tomar los parámetros directamente del diccionario params
        # size = params.get("size")
        # plan = params.get("plan")
        # body = {
        #     "size": size,
        #     "plan": plan
        # }
        try:
            tipo = params.get("type", "public")
            url = f"{API_URL}/{APP_ID}/select?type={tipo}"
            headers = {"Content-Type": "application/json",
                       "Edamam-Account-User": "juanjomg"}
            response = requests.post(
                url,
                json=params,
                headers=headers,
                timeout=20
            )
            # Log detallado para depuración
            print(f"URL: {url}")
            print(f"Response text: {response.text}")
            if response.status_code == 200:
                return response.json()
            else:
                return response.text
        except Exception as e:
            return {"error": str(e)}
