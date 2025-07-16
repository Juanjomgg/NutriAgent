# Herramientas de integración con APIs de nutrición
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv('APP_EDAMAM_ID')
API_KEY = os.getenv('API_EDAMAM_KEY')

class EdamamMealPlannerTool:

    def __init__(self):

        self.base_url = "https://api.edamam.com/api/meal-planner/v1"
        self.api_id = APP_ID
        self.api_key = API_KEY
        self.headers = {
            "Content-Type": "application/json",
            "Edamam-Account-User": "juanjomg"
        }

    async def run(self, params: dict):
        """
        Crea un plan de comidas usando la API Meal Planner de Edamam.
        Espera un diccionario params con la estructura compatible con la API Edamam.
        """

        try:
            tipo = params.get("type", "public")
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/{self.api_id}/select?type={tipo}"
                response = await client.post(
                    url,
                    json=params,
                    headers=self.headers,
                    timeout=20.0
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": response.text}
        except httpx.TimeoutException as e:
            return {"error": f"Timeout error: {str(e)}"}
        except httpx.RequestError as e:
            return {"error": f"Request error: {str(e)}"}
        except httpx.HTTPStatusError as e:
            return Exception(f"HTTP error: {e.response.status_code} - {e.response.text}")
