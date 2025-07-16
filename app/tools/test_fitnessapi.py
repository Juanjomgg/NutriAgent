import asyncio
from app.tools.fitness_apis import ExerciseDBTool

if __name__ == "__main__":
    params = {
        "action": "get_by_target",
        "target": "chest",
    }

    resultado = asyncio.run(ExerciseDBTool().run(**params))
    print("Resultado ExerciseDBTool:")
    print(resultado)
