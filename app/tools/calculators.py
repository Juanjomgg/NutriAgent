# Herramientas de cálculo nutricional

class MacroCalculatorTool:
    name = "MacroCalculatorTool"
    def run(self, params: dict):
        """
        Calcula la distribucion de proteinas, grasas y carbohidratos en gramos, pasandole
        una cantidad de calorías y el porcentajes de proteinas, grasas y carbohidratos que
        queremos que provengan de dichos macronutientes.
        Parámetros esperados en params:
            calorias (int), proteina_pct (int), grasa_pct (int), carb_pct (int)
        Retorna gramos de cada macro.
        """
        kwargs = params or {}
        calorias = kwargs.get("calorias", 2000)
        proteina_pct = kwargs.get("proteina_pct", 20)
        grasa_pct = kwargs.get("grasa_pct", 30)
        carb_pct = kwargs.get("carb_pct", 50)
        # 1g proteína = 4 kcal, 1g carbo = 4 kcal, 1g grasa = 9 kcal
        proteina_g = round((calorias * proteina_pct / 100) / 4)
        grasa_g = round((calorias * grasa_pct / 100) / 9)
        carb_g = round((calorias * carb_pct / 100) / 4)
        return {
            "calorias": calorias,
            "proteina_g": proteina_g,
            "grasa_g": grasa_g,
            "carb_g": carb_g
        }

class CalorieCalculatorTool:
    name = "CalorieCalculatorTool"
    def run(self, params: dict):
        """
        Calcula calorías diarias recomendadas usando Harris-Benedict.
        Parámetros esperados en params:
            sexo (str), edad (int), peso (kg), altura (cm), actividad (str)
        """
        kwargs = params or {}
        sexo = kwargs.get("sexo", "masculino")
        edad = kwargs.get("edad", 30)
        peso = kwargs.get("peso", 70)
        altura = kwargs.get("altura", 175)
        actividad = kwargs.get("actividad", "moderado")
        if sexo == "masculino":
            tmb = 88.36 + (13.4 * peso) + (4.8 * altura) - (5.7 * edad)
        else:
            tmb = 447.6 + (9.2 * peso) + (3.1 * altura) - (4.3 * edad)
        factores = {
            "sedentario": 1.2,
            "ligero": 1.375,
            "moderado": 1.55,
            "activo": 1.725,
            "muy activo": 1.9
        }
        factor = factores.get(actividad, 1.55)
        calorias = int(tmb * factor)
        return {
            "tmb": round(tmb),
            "calorias_mantenimiento": calorias,
            "actividad": actividad
        }

class WorkoutCalculatorTool:
    name = "WorkoutCalculatorTool"
    def run(self, params: dict):
        """
        Genera una rutina semanal básica según nivel y objetivo.
        Parámetros esperados en params:
            nivel (str): 'principiante', 'intermedio', 'avanzado'
            objetivo (str): 'fuerza', 'hipertrofia', 'resistencia'
        """
        kwargs = params or {}
        nivel = kwargs.get("nivel", "principiante")
        objetivo = kwargs.get("objetivo", "fuerza")
        rutina = []
        if nivel == "principiante":
            rutina = [
                "Lunes: Full body",
                "Miércoles: Full body",
                "Viernes: Full body"
            ]
        elif nivel == "intermedio":
            rutina = [
                "Lunes: Tren superior",
                "Martes: Tren inferior",
                "Jueves: Tren superior",
                "Viernes: Tren inferior"
            ]
        else:
            rutina = [
                "Lunes: Pecho/Espalda",
                "Martes: Piernas",
                "Miércoles: Hombros/Brazos",
                "Jueves: Piernas",
                "Viernes: Full body"
            ]
        return {
            "nivel": nivel,
            "objetivo": objetivo,
            "rutina": rutina
        }
