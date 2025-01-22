from aiogram import Router
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import Form, WorkoutQuestion, FoodQuestion
import aiohttp
import datetime

import utils 

router = Router()

# Обработчик команды /start
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply("Добро пожаловать! Я ваш бот.\nВведите /help для списка команд.")

# Обработчик команды /help
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.reply(
        "Доступные команды:\n"
        "/start - Начало работы\n"
        "/set_profile - Заполнение профиля\n"
        "/update_calorie_goal <Число калорий> - Изменение цели по калориям\n"
        "/log_water <Количество воды в мл> - Трекинг воды\n"
        "/log_workout <Тип тренировки> <Время в мин> - Трекинг тренировок\n"
        "/log_food <еда> - Трекинг еды\n"
        "/check_progress - Калории и вода за текущий день\n"
    )


# Заполнение профиля
@router.message(Command("set_profile"))
async def start_form(message: Message, state: FSMContext):
    await message.reply("Введите ваш вес (в кг):")
    await state.set_state(Form.weight)

@router.message(Form.weight)
async def process_weight(message: Message, state: FSMContext):
    await state.update_data(weight=message.text)
    await message.reply("Введите ваш рост (в см):")
    await state.set_state(Form.height)

@router.message(Form.height)
async def process_height(message: Message, state: FSMContext):
    await state.update_data(height=message.text)
    await message.reply("Введите ваш возраст:")
    await state.set_state(Form.age)

@router.message(Form.age)
async def process_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.reply("Сколько минут физической активности у вас в день?")
    await state.set_state(Form.activity_min)

@router.message(Form.activity_min)
async def process_activity_min(message: Message, state: FSMContext):
    await state.update_data(activity_min=message.text)
    await message.reply("В каком городе вы живете?")
    await state.set_state(Form.city)

@router.message(Form.city)
async def finish_profile(message: Message, state: FSMContext):
    await state.update_data(city=message.text)

    user_id = message.from_user.id

    data = await state.get_data()
    package = {}

    package['user_id'] = user_id
    package['city'] = data.get("city")
    try:
        package['height'] = int(data.get("height"))
        package['weight'] = int(data.get("weight"))
        package['age'] = int(data.get("age"))
        package['activity_min'] = int(data.get("activity_min"))
    except Exception as e:
        await message.reply("Заполнить профиль не удалось. Пожалуйста, перезаполните профиль.\n"
                            "Учтите, что в параметрах 'Возраст', 'Рост', 'Вес' и 'Время активности' можно использовать только целые числа.\n")
        await state.clear()
        return 0
    
    package['water_goal'] = 30 * package['weight']
    package['calorie_goal'] = int(88.4 + (13.4 * package['weight']) + (4.8 * package['height']) - (5.7 * package['age']))
    package['last_update'] = datetime.datetime.now()

    try:
        cur_profile = await utils.get_profile_from_db(user_id)
        if cur_profile is None:
            await utils.add_profile_to_db(package)
        else:
            await utils.update_profile_to_db(package)
    except Exception as e:
        print(e)
        await message.reply('Что-то пошло не так.')
        return 0

    if cur_profile is None:
        await message.reply("Ваш профиль успешно заполнен!")
    else:
        await message.reply("Ваш профиль успешно обновлен!")

    await message.reply(f"Ваша базовая норма воды {package['water_goal']} мл. Она может увеличиться от погоды и ваших тренировок.\n"
                        f"Ваша базовая норма калорий {package['calorie_goal']} ккал. Она может увеличиться от ваших тренировок.\n"
                        f"Для того, чтобы поменять свою норму калорий, используйте /update_calorie_goal.\n"
                        "Для полных норм на текущий день используйте /check_progress.")
    await state.clear()


# Log water
@router.message(Command("log_water"))
async def log_water(message: Message):
    user_id = message.from_user.id

    try:
        amount = message.text.split()[1] 
    except Exception as e:
        await message.reply("Кажется, вы забыли параметры))")
        return 0

    date_time = datetime.datetime.now()

    package = {'user_id': user_id, 'amount': amount, 'time': date_time}

    await utils.log_water_to_db(package)

    await message.reply(f"{amount} мл воды затрекано")


# Log food
@router.message(Command("log_food"))
async def log_food(message: Message, state: FSMContext):
    try:
        food_name = ' '.join(message.text.split()[1:]) 
    except Exception as e:
        await message.reply("Кажется, вы забыли параметры))")
        return 0

    await state.update_data(food=food_name)
    
    calories = await utils.get_calories_per_food(food_name)

    if calories == 0:
        await message.reply("К сожалению, в нашей базе данных нет калорийности для этой еды.\n"
                            "Пожалуйста, оцените (прогуглите) количество калорий, содержащееся в 100 граммах этого продукта.\n")
        await state.set_state(FoodQuestion.estimate_calories)
    else:
        await state.update_data(estimate_calories=calories)
        await message.reply(f"Мы оценили {food_name} в {calories} ккал/100 грамм.\n"
                            f"Сколько грамм вы примерно съели?\n")
        await state.set_state(FoodQuestion.amount)

        
@router.message(FoodQuestion.estimate_calories)
async def ask_estimate_food_calories(message: Message, state: FSMContext):   
    ccal_number = utils.extract_number(message.text)

    if ccal_number is None:
        await message.reply("Не удалось получить из вашего сообщения калорийность.\n"
                            "Пожалуйста, перезапустите команду \log_food и ответьте целым числом.\n")
        await state.clear()
    else:
        await state.update_data(estimate_calories=ccal_number)

        await message.reply(f"Сколько грамм вы примерно съели?\n")
        await state.set_state(FoodQuestion.amount)


@router.message(FoodQuestion.amount)
async def ask_estimate_food_amount(message: Message, state: FSMContext):   
    amount_number = utils.extract_number(message.text)

    await state.update_data(amount=amount_number)

    if amount_number is None:
        await message.reply("Не удалось получить из вашего сообщения количество еды.\n"
                            "Пожалуйста, перезапустите команду \log_food и ответьте целым числом.\n")
    else:
        user_id = message.from_user.id
        data = await state.get_data()
        food = data.get('food')
        estimate_calories = data['estimate_calories']

        calories = estimate_calories * amount_number // 100

        package = {'user_id': user_id, 'food': food, 'amount': amount_number, 'calories': estimate_calories, 'time': datetime.datetime.now()}

        await utils.log_food_to_db(package)

        await message.reply(f"Ваш прием пищи залогирован.\n"
                            f"Вы съели {calories} ккал.\n")
    
    await state.clear()


# Log training
@router.message(Command("log_workout"))
async def log_workout(message: Message, state: FSMContext):
    try:
        workout_type, duration = message.text.split()[1], message.text.split()[2]
    except Exception as e:
        await message.reply("Кажется, вы забыли параметры))")
        return 0

    try:
        duration = int(duration)
    except Exception as e:
        await message.reply("Длительность тренировки должна быть целым количеством минут.")
        return 0

    calories = await utils.get_calories_per_workout(workout_type)

    if calories == 0:
        await message.reply("К сожалению, в нашей базе данных нет такого вида тренировок.\n"
                            "Пожалуйста, оцените (прогуглите) количество калорий, которое сжигается за час тренировок этим спортом.\n")
        await state.update_data(workout_type=workout_type)
        await state.update_data(duration=duration)
        await state.set_state(WorkoutQuestion.estimate_calories)
    else:
        spent_calories = calories * duration // 60
        user_id = message.from_user.id
        date_time = datetime.datetime.now()
        package = {'user_id': user_id, 'workout_type': workout_type, 'amount_min': duration, 'calorie_amount': spent_calories, 'time': date_time}
        await utils.log_workout_to_db(package)

        await message.reply(f"Мы оценили вашу активность в {calories} ккал в час.\n"
                            f"Вы сожгли {spent_calories} ккал ! Omega motivational speech here.\n")


@router.message(WorkoutQuestion.estimate_calories)
async def ask_estimate_workout_calories(message: Message, state: FSMContext):
    await state.update_data(calories=message.text)
    
    ccal_number = utils.extract_number(message.text)

    if ccal_number is None:
        await message.reply("Не удалось получить из вашего сообщения калорийность.\n"
                            "Пожалуйста, перезапустите команду \log_food и ответьте целым числом.\n")
    else:
        data = await state.get_data()

        duration = data.get("duration")
        workout_type = data.get("workout_type")
        spent_calories = ccal_number * duration // 60
        user_id = message.from_user.id
        date_time = datetime.datetime.now()

        package = {'user_id': user_id, 'workout_type': workout_type, 'amount_min': duration, 'calorie_amount': spent_calories, 'time': date_time}
        await utils.log_workout_to_db(package)

        await message.reply(f"Вы сожгли {spent_calories} ккал ! Omega motivational speech here.\n")
        await state.clear()


# Check current progress
@router.message(Command("check_progress"))
async def check_progress(message: Message):
    user_id = message.from_user.id

    calorie_count, water_count, training_calories, training_mins = await utils.get_progress_from_db(user_id)

    await message.reply(f"За сегодня вы затрекали {int(calorie_count)} калорий и {int(water_count)} мл воды.")

    profile = await utils.get_profile_from_db(user_id)

    if profile is None:
        await message.reply("Кажется, вы не заполнили профиль и у вас нет целей по воде и калориям \n"
                            "Для того, чтобы они появились используйте команду /set_profile \n")
    else:
        weight = profile[2]
        city = profile[5]
        water_goal = profile[6]
        calorie_goal = profile[7]

        temp = await utils.get_weather(city)
        if temp is None:
            temp_adj = 0
        else:
            temp_adj = max(0, 0.2 * weight * int(temp))

        await message.reply("Ваша цель по воде на сегодняшний день:\n"
                            f"Базовая: {water_goal} мл\n"
                            f"Из-за погоды: + {temp_adj} мл\n"
                            f"Из-за тренировок: + {(training_mins * 20) // 6} мл\n"
                            f"Итого: {water_goal + temp_adj + (training_mins * 20) // 6} мл.\n")
        await message.reply("Ваша цель по калориям на сегодняшний день:\n"
                    f"Базовая: {calorie_goal} ккал\n"
                    f"Из-за тренировок: + {training_calories} ккал \n"
                    f"Итого: {calorie_goal + training_calories} ккал\n")
        
        utils.generate_graph(water=int(water_count), water_goal=water_goal, calorie_goal=calorie_goal, calories=int(calorie_count))
        
        await message.answer_photo(photo=FSInputFile('graph.jpg', filename='Graph'), caption='')


# Update calorie goal
@router.message(Command("update_calorie_goal"))
async def update_calorie_goal(message: Message):
    user_id = message.from_user.id
    try:
        calorie_goal = message.text.split()[1] 
    except Exception as e:
        await message.reply("Кажется, вы забыли параметры))")
        return 0

    try:
        calorie_goal = int(calorie_goal)
    except Exception as e:
        await message.reply(f"Не удалось изменить цель по ккал. Обратите внимание, что количество должно быть целым числом.")

    await utils.update_calorie_goal_to_db(user_id, calorie_goal)

    await message.reply(f"Ваша новая цель: {str(calorie_goal)} ккал")


# Функция для подключения обработчиков
def setup_handlers(dp):
    dp.include_router(router)
