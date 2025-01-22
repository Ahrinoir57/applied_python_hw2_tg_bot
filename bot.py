import asyncio
from aiogram import Bot, Dispatcher
from config import TG_TOKEN
from handlers import setup_handlers
from middlewares import LoggingMiddleware
import aiosqlite
import os


create_table_statements = [ 
    """CREATE TABLE IF NOT EXISTS Profiles (
            user_id INTEGER PRIMARY KEY, 
            height INT NOT NULL, 
            weight INT NOT NULL, 
            age INT NOT NULL, 
            activity_min INT NOT NULL,
            city TEXT NOT NULL,
            water_goal INT NOT NULL,
            calorie_goal INT NOT NULL,
            last_update DATE NOT NULL
        );""",

    """CREATE TABLE IF NOT EXISTS Logged_Water (
            user_id INT NOT NULL, 
            amount INT NOT NULL, 
            update_time DATE NOT NULL, 
            FOREIGN KEY (user_id) REFERENCES profiles (user_id)
        );""",

    """CREATE TABLE IF NOT EXISTS Logged_Food (
            user_id INT NOT NULL, 
            food TEXT NOT NULL,
            amount INT NOT NULL, 
            overall_calories INT NOT NULL, 
            update_time DATE NOT NULL, 
            FOREIGN KEY (user_id) REFERENCES profiles (user_id)
        );""",

    """CREATE TABLE IF NOT EXISTS Logged_Workout (
            user_id INT NOT NULL, 
            workout_type TEXT NOT NULL,
            amount_min INT NOT NULL, 
            calorie_amount INT NOT NULL, 
            update_time DATE NOT NULL, 
            FOREIGN KEY (user_id) REFERENCES profiles (user_id)
        );"""
]


# Создаем экземпляры бота и диспетчера
bot = Bot(token=TG_TOKEN)
dp = Dispatcher()

# Настраиваем middleware и обработчики
dp.message.middleware(LoggingMiddleware())
setup_handlers(dp)

async def main():
    # Create database if not present
    if not os.path.isdir('./database/'):
        os.makedirs('./database/')
        async with aiosqlite.connect("./database/test.db") as conn:
            for statement in create_table_statements:
                await conn.execute(statement)

            await conn.commit()


    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
