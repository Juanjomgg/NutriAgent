# Herramientas de integración con APIs de nutrición
import requests
import os
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv('APP_EDAMAM_ID')
API_KEY = os.getenv('API_EDAMAM_KEY')

class EdamamMealPlannerTool:

    def run(self, params: dict):
        """
        Crea un plan de comidas usando la API Meal Planner de Edamam.
        Espera un diccionario params con la estructura compatible con la API Edamam.
        """

        self.base_url = "https://api.edamam.com/api/meal-planner/v1"

        try:
            tipo = params.get("type", "public")
            url = f"{self.base_url}/{APP_ID}/select?type={tipo}"
            headers = {"Content-Type": "application/json",
                       "Edamam-Account-User": "juanjomg"}
            response = requests.post(
                url,
                json=params,
                headers=headers,
                timeout=20
            )

            if response.status_code == 200:
                return response.json()
            else:
                return response.text
        except Exception as e:
            return {"error": str(e)}
