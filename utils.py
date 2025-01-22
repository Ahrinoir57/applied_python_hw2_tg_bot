import aiohttp
from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import aiosqlite
import json
import re

def extract_number(text):
    match = re.search(r'\b(\d+)\b', text)
    if match:
        return int(match.group(1))
    else:
        return None


async def get_weather(city: str):
    with open('tokens.json') as f:
        tokens = json.load(f)
        api_key = tokens['open_weather']

    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric') as response:
            data = await response.json()

    try:
        t = data['main']['temp']
    except Exception as e:
        t = None
    
    return t


async def get_calories_per_workout(workout_type: str):
    with open('tokens.json') as f:
        tokens = json.load(f)
        api_key = tokens['ninja']

    api_url = 'https://api.api-ninjas.com/v1/caloriesburned?activity={}'.format(workout_type)

    async with aiohttp.ClientSession(headers={'X-Api-Key': api_key}) as session:
        async with session.get(api_url) as response:
            data = await response.json()

    if len(data) == 0:
        return 0
    else:
        return data[0]['calories_per_hour']
    

async def get_calories_per_food(food: str):
    with open('tokens.json') as f:
        tokens = json.load(f)
        api_key = tokens['calories']

    api_url = 'https://api.calorieninjas.com/v1/nutrition?query={}'.format(food)

    async with aiohttp.ClientSession(headers={'X-Api-Key': api_key}) as session:
        async with session.get(api_url) as response:
            data = await response.json()

    if len(data['items']) == 0:
        return 0
    else:
        return data['items'][0]['calories']
    

async def log_water_to_db(data):
    async with aiosqlite.connect("./database/test.db") as db:
        cursor = await db.cursor()
        await cursor.execute("""INSERT INTO Logged_Water (user_id, amount, update_time)
                              VALUES (?,?,?)""", (data['user_id'], data['amount'], data['time']))
        await db.commit()
        await cursor.close()


async def log_food_to_db(data):
    async with aiosqlite.connect("./database/test.db") as db:
        cursor = await db.cursor()
        await cursor.execute("""INSERT INTO Logged_Food (user_id, food, amount, overall_calories, update_time)
                              VALUES (?,?,?,?,?)""", (data['user_id'], data['food'], data['amount'], data['calories'], data['time']))
        await db.commit()
        await cursor.close()


async def log_workout_to_db(data):
    async with aiosqlite.connect("./database/test.db") as db:
        cursor = await db.cursor()
        await cursor.execute("""INSERT INTO Logged_Workout (user_id, workout_type, amount_min, calorie_amount, update_time)
                              VALUES (?,?,?,?,?)""", (data['user_id'], data['workout_type'], data['amount_min'], data['calorie_amount'], data['time']))
        await db.commit()
        await cursor.close()
    pass


async def get_progress_from_db(user_id):
    calorie_count = 0
    water_count = 0
    training_calories_burnt = 0
    training_mins = 0
    async with aiosqlite.connect("./database/test.db") as db:
        async with db.execute(f"SELECT amount FROM Logged_Water WHERE user_id = {user_id} AND DATE(update_time) = DATE('now')") as cursor:
            async for row in cursor:
                water_count += row[0]

        async with db.execute(f"SELECT overall_calories FROM Logged_Food WHERE user_id = {user_id} AND DATE(update_time) = DATE('now')") as cursor:
            async for row in cursor:
                calorie_count += row[0]

        async with db.execute(f"SELECT calorie_amount, amount_min FROM Logged_Workout WHERE user_id = {user_id} AND DATE(update_time) = DATE('now')") as cursor:
            async for row in cursor:
                training_calories_burnt += row[0]
                training_mins += row[1]

    return calorie_count, water_count, training_calories_burnt, training_mins


async def get_profile_from_db(user_id):
    async with aiosqlite.connect("./database/test.db") as db:
        async with db.execute(f"SELECT * FROM Profiles WHERE user_id = {user_id}") as cursor:
            rows = await cursor.fetchall()
            
            if len(rows) <= 0:
                return None
            else:
                result = rows[0]
                return result


async def add_profile_to_db(data):
    async with aiosqlite.connect("./database/test.db") as db:
        cursor = await db.cursor()
        await cursor.execute("""INSERT INTO Profiles (user_id, height, weight, age, activity_min, city, water_goal, calorie_goal, last_update)
                              VALUES (?,?,?,?,?,?,?,?,?)""", (data['user_id'], data['height'], data['weight'], data['age'], data['activity_min'], data['city'], data['water_goal'], data['calorie_goal'], data['last_update']))
        await db.commit()
        await cursor.close()


async def update_profile_to_db(data):
    async with aiosqlite.connect("./database/test.db") as db:
        cursor = await db.cursor()
        await cursor.execute('''UPDATE Profiles SET height = ?, weight = ?, age = ?,
                              activity_min = ?, city = ?, water_goal = ?, calorie_goal = ?,
                              last_update = ? WHERE user_id = ?''',
                            (data['height'], data['weight'], data['age'], data['activity_min'], data['city'], data['water_goal'], data['calorie_goal'], data['last_update'], data['user_id']))
        await db.commit()
        await cursor.close()


async def update_calorie_goal_to_db(user_id, goal):
    async with aiosqlite.connect("./database/test.db") as db:
        cursor = await db.cursor()
        await cursor.execute(f"""UPDATE Profiles
                                SET calorie_goal = {goal}
                                WHERE user_id = {user_id}; """)
        await db.commit()
        await cursor.close()