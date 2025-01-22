from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    name = State()
    age = State()
    weight = State()
    height = State()
    activity_min = State()
    city = State()


class WorkoutQuestion(StatesGroup):
    workout_type = State()
    duration = State()
    estimate_calories = State()

class FoodQuestion(StatesGroup):
    amount = State()
    estimate_calories = State()
    food = State()
    
