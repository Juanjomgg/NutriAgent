from app.tools.nutrition_apis import EdamamMealPlannerTool

if __name__ == "__main__":
    params = {
        "size": 3,
        "plan": {
            "accept": {
                "all": [
                    {
                        "health": [
                            "SOY_FREE",
                            "FISH_FREE",
                            "MEDITERRANEAN"
                        ]
                    }
                ]
            },
            "fit": {
                "ENERC_KCAL": {
                    "min": 1000,
                    "max": 2000
                },
                "SUGAR.added": {
                    "max": 20
                }
            }
        }
    }
    resultado = EdamamMealPlannerTool().run(params)
    print("Resultado EdamamMealPlannerTool:")
    print(resultado)
