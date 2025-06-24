# NutriCoach: Agente de Nutrición Inteligente

NutriCoach es un agente conversacional de nutrición construido con [LangChain](https://python.langchain.com/) y [OpenAI Chat](https://platform.openai.com/docs/guides/gpt). Permite responder consultas sobre alimentación, calcular macronutrientes y calorías, recomendar alimentos y generar planes nutricionales personalizados, integrando varias APIs y herramientas especializadas.

## Características

- Responde preguntas sobre nutrición y alimentos.
- Calcula calorías y macronutrientes según el perfil del usuario.
- Genera planes de alimentación personalizados.
- Integra múltiples fuentes de datos (APIs de nutrición, calculadoras, etc).
- Considera restricciones dietéticas, alergias y objetivos personales.
- Fácilmente extensible con nuevas herramientas.

## Estructura del Proyecto

```
containerNutriCoach/
  app/
    agents/
      nutrition_agent.py      # Lógica principal del agente de nutrición
    tools/
      nutrition_apis.py       # Integración con APIs externas (USDA, Spoonacular, etc)
      calculators.py          # Herramientas de cálculo nutricional
    ...
  requirements.txt
```

## Instalación

1. Clona el repositorio y entra en el directorio del proyecto.
2. Crea un entorno virtual e instala las dependencias:
   ```powershell
   python -m venv env
   .\env\Scripts\activate
   pip install -r requirements.txt
   ```
3. Configura tus claves de API necesarias (por ejemplo, OpenAI, Spoonacular, USDA) como variables de entorno.

## Uso

El agente principal está en `app/agents/nutrition_agent.py`. Puedes integrarlo en un backend FastAPI, Django, o ejecutarlo en scripts asíncronos.

Ejemplo de uso básico:

```python
from app.agents.nutrition_agent import NutritionAgent
import asyncio

agent = NutritionAgent()
user_profile = {
    "age": 30,
    "weight": 70,
    "height": 175,
    "activity_level": "moderado",
    "goals": "perder peso",
    "restrictions": "sin gluten"
}
message = "¿Qué debo comer para perder peso esta semana?"

result = asyncio.run(agent.process(message, user_profile, context=[]))
print(result["content"])
```

## Extensión

Puedes añadir nuevas herramientas creando clases que hereden de `BaseTool` en la carpeta `tools/` y agregándolas a la lista `self.tools` en `NutritionAgent`.

## Dependencias principales

- langchain
- langchain-openai
- openai
- (APIs externas: USDA, Spoonacular, etc.)

Consulta `requirements.txt` para la lista completa.

## Notas

- El agente está diseñado para ser usado como backend conversacional, pero puede integrarse en aplicaciones web, móviles o asistentes personales.
- Personaliza los prompts y herramientas según tus necesidades.
