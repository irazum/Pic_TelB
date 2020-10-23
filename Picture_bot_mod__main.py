'''
~~!!update handler of API-telegram and main!!~~
'''
from Pic_bot_loader_async import *

from aiogram import Bot, Dispatcher, executor, types
from datetime import datetime, time, timedelta, timezone

token_telegram_bot = config.telegram_bot_token
# configure debugger
logging.basicConfig(level=logging.INFO)
# initialization of Bot class
bot = Bot(token=token_telegram_bot)
# initialization of updates (messages) handler class
dp = Dispatcher(bot)

# likes photo dict {file_id:author}
likes_photo_dct = dict()
# statistics dicts
users_stat = dict()
users_stat_mes = dict()
categories_stat = dict()
time_stat = dict()


def stat_writing(callback_query: types.callback_query.CallbackQuery):
    """
    records statistics in stat dicts - "user_stat", "categories_stat", "time_stat"
    called from callback query handlers
    :param callback_query:
    :return: None
    """
    users_stat[callback_query.from_user.id] = users_stat.get(
        callback_query.from_user.id, 0
    ) + 1
    categories_stat[callback_query.data] = categories_stat.get(
        callback_query.data, 0
    ) + 1
    time = datetime.now(tz=timezone(timedelta(hours=3))).time().hour
    time_stat[time] = time_stat.get(time, 0) + 1


async def insert_update_db(table: str, input_data: dict, column_names: list) -> None:
    """
    fills statistics tables in a database
    :param table: table name
    :param input_data: {value for first column_names element: value for second column_names element, ...}
    :param column_names: list of 2 special column names [id or unique column, counter column]
    :return: None
    """
    for key, value in input_data.items():
        input_dct = dict()
        input_dct[column_names[0]] = key
        input_dct[column_names[1]] = value
        insert_result = db.insert_one(table, input_dct)
        if insert_result is not None:
            if ("Duplicate entry" in insert_result):
                current_value = db.select_simple(table, [column_names[1]], {column_names[0]: key})[0][0]
                db.update_simple_one(
                    table,
                    column_names[1],
                    (value if current_value is None else current_value + value),
                    {column_names[0]: key}
                )
            elif "foreign key constraint" in insert_result:
                print(f"!!Error_db!!: FOREIGN KEY constraint failed\ntable: {table}, input_dct: {input_dct}")
                await bot.send_message(input_dct['user_id'], 'Appeared a problem\nplease, enter "/start"\nthank you!')


@dp.message_handler(commands=[config.statistics_user_1])
async def statistics_user_1_func(message):
    '''
    special (current statistics) command handler for admins
    :param message:
    :return:
    '''
    mes1 = f'активных пользоавтелей: {len(users_stat)}'
    mes2 = f'всего запросов картинок за сессию: {sum(users_stat.values())}'
    users_stat_lst = sorted(users_stat.items(), key=lambda x: (x[1], x[0]), reverse=True)[:5:]
    # top 5 active users [[first_name, number_of_send_messages, number_of_requests_photo]...]
    data = list()
    for item in users_stat_lst:
        first_name = db.select_simple("users", ["first_name"], {"id": item[0]})[0][0]
        data.append([first_name, users_stat_mes.get(item[0], 0), item[1]])
    mes3 = str()
    for item in data:
        mes3 = f"{mes3}\n{' - '.join([str(k) for k in item])}"
    # проверка, не пытается ли кто хакнуть мои служебные комманды + на DoS
    us_mes_lst = sorted(users_stat_mes.items(), key=lambda x: x[1], reverse=True)[:1:]
    mes4 = str()
    if len(us_mes_lst) > 0:
        first_name = db.select_simple("users", ["first_name"], {"id": us_mes_lst[0][0]})[0][0]
        mes4 = f'top mes.: {first_name}: {us_mes_lst[0][1]}'

    await message.reply(f'{mes1}\n{mes2}\n{mes3}\n\n{mes4}', reply=False)


@dp.message_handler(commands=[config.statistics_categories_1])
async def statistics_categories_1_func(message):
    '''
    special (current statistics) command handler for admins
    :param message:
    :return:
    '''
    categories_stat_lst = sorted(categories_stat.items(), key=lambda x: (x[1], x[0]), reverse=True)[:5:]
    mes = "statistics\n"
    for item in categories_stat_lst:
        mes += f"{item[0]}: {item[1]}\n"
    await message.reply(mes, reply=False)


@dp.message_handler(commands=[config.statistics_time_1])
async def statistics_time_1_func(message):
    '''
    special (current statistics) command handler for admins
    :param message:
    :return:
    '''
    time_stat_lst = sorted(time_stat.items(), key=lambda x: (x[1], x[0]), reverse=True)
    mes = "statistics\n"
    for item in time_stat_lst:
        mes += f"{item[0]} ч.: {item[1]}\n"
    await message.reply(mes, reply=False)


@dp.message_handler(commands=[config.statistics_user_2])
async def statistics_user_2_func(message):
    '''
    special (all-time statistics) command handler for admins
    :param message:
    :return:
    '''
    mes1 = f"всего юзеров: {db.select_simple('users', ['count(id)'])[0][0]}"
    data = db.select_inner_join_simple(
        "stat_users",
        'users',
        ("user_id", "id"),
        ["first_name", "last_name", "language_code", "messages_number", "requests_number"]
    )
    mes2 = str()
    for item in sorted(data, key=lambda x: x[4], reverse=True)[:5:]:
        mes2 += f"\n{'-'.join([str(i) for i in item])}"

    await message.reply(f"{mes1}\n{mes2}", reply=False)


@dp.message_handler(commands=[config.statistics_categories_2])
async def statistics_categories_2_func(message):
    '''
    special (all-time statistics) command handler for admins
    :param message:
    :return:
    '''
    data = db.select_simple("stat_categories", ["category", "requests_number"])
    mes = "statistics\n"
    for item in sorted(data, key=lambda x: x[1], reverse=True):
        mes += f"{': '.join([str(i) for i in item])}\n"
    if len(mes) >= 4096:
        for i in range(len(mes) // 4096):
            await message.reply(mes[i * 4096: (i + 1) * 4096:], reply=False)
    await message.reply(mes[(len(mes) // 4096) * 4096: len(mes) + 1:], reply=False)


@dp.message_handler(commands=[config.statistics_time_2])
async def statistics_time_2_func(message):
    '''
    special (all-time statistics) command handler for admins
    :param message:
    :return:
    '''
    data = db.select_simple("stat_time", ["time", "requests_number"])
    mes = "statistics\n"
    for item in sorted(data, key=lambda x: x[1], reverse=True):
        mes += f"\n{'ч.: '.join([str(i) for i in item])}"
    await message.reply(mes, reply=False)


@dp.message_handler(commands=[config.statistics_likes])
async def statistics_time_2_func(message):
    '''
    special (statistics) command handler for admins
    :param message:
    :return:
    '''
    mes = f"всего лайков: {db.select_simple('likes_photo', ['sum(likes_number)'])[0][0]}"
    await message.reply(mes, reply=False)


# обработчики базовых команд
@dp.message_handler(commands=['start', 'help', 'помощь'])
async def send_help(message: types.Message):
    '''
    commands handler
    :param message:
    :return:
    '''
    if message.from_user.language_code == 'ru':
        help_message = '''
        Привет!
        Этот бот создан для того, чтобы отправлять вам случайные высококлассные фото в хорошем качестве.
        Пожалуйста, введите любое сообщение в этот чат или нажмите кнопку "Показать категории", чтобы выбрать категорию фото, которое вы хотите посмотреть.
        Каждый раз вам будет досупно для выбора 3 случайных категории из нашей подборки. 
        Нажмайте на ❤ под понравившемся фото, чтобы получить ссылку на это фото в оригинальном качестве.
        Фото предоставлены API pexels.com.
        Также доступны команды: 
    /все - выводит все доступные категории, а не 3 случайные.
    /помощь - выводит приветственное сообщение ещё раз 
        Итак, ВВЕДИТЕ ЛЮБОЕ СООБЩЕНИЕ!
        '''
    else:
        help_message = '''
        Hi!
        This bot sends you random high-quality photos.
        Please enter any message into this chat or press button "Show categories" and you will be able to choose the category of photo that you want to see.
        Each time you will be available to choose 3 random categories from our selection.
        Press ❤ under the photo you like to get a link to this photo in original quality.
        Photos taken using pexels.com API.
        Available commands:
    /all - shows all available categories, not 3 random ones.
    /help - send a welcome message again
        So, ENTER ANY MESSAGE!
        '''
    if message.from_user.language_code == 'ru':
        button_r = types.KeyboardButton("Показать категории")
    else:
        button_r = types.KeyboardButton("Show categories")
    markup_r = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup_r.add(button_r)
    await message.reply(help_message.strip(), reply=False, reply_markup=markup_r)
    # added a new user in data base
    db.insert_one(
        'users',
        {'id': message.from_user.id, 'is_bot': message.from_user.is_bot,
         'first_name': message.from_user.first_name, 'last_name': message.from_user.last_name,
         'language_code': message.from_user.language_code}
    )


@dp.message_handler(commands=['fuck', 'fuckyou'])
@dp.message_handler(lambda message: (message.text.lower() == 'fuck you') or (message.text.lower() == 'fuck'))
async def send_on_fuck(message):
    '''
    easter egg
    :param message:
    :return:
    '''
    await message.reply('I like you, motherfucker', reply=False)
    print(message.from_user)


@dp.message_handler(commands=['all', 'все'])
async def send_all_categories(message):
    '''
    commands handler
    :param message:
    :return:
    '''
    buttons = []
    if message.from_user.language_code == 'ru':
        for category in categories_lst:
            buttons.append(
                types.InlineKeyboardButton(
                    categories_translate_dict[category],
                    callback_data=category
                )
            )
        text = 'Выбери категорию фото!'
    else:
        for category in categories_lst:
            buttons.append(types.InlineKeyboardButton(category, callback_data=category))
        text = 'Choose photo category!'

    markup = types.InlineKeyboardMarkup().add(*buttons)
    await message.reply(text, reply_markup=markup, reply=False)


@dp.message_handler(lambda message: message.text == "Показать категории" or message.text == "Show categories")
async def inline_key_board_markup(message):
    '''
    ReplyKeybodardMarkup1 button handler
    :param message:
    :return:
    '''
    # перемешиваем категории
    categories_mixed = r.sample(categories_lst, len(categories_lst))
    # Создаём объекты встроенной клавиатуры
    if message.from_user.language_code == 'ru':
        button1 = types.InlineKeyboardButton(
            categories_translate_dict[categories_mixed[0]],
            callback_data=categories_mixed[0]
        )
        button2 = types.InlineKeyboardButton(
            categories_translate_dict[categories_mixed[1]],
            callback_data=categories_mixed[1]
        )
        button3 = types.InlineKeyboardButton(
            categories_translate_dict[categories_mixed[2]],
            callback_data=categories_mixed[2]
        )
        text = 'Выбери категорию фото!'
    else:
        button1 = types.InlineKeyboardButton(categories_mixed[0], callback_data=categories_mixed[0])
        button2 = types.InlineKeyboardButton(categories_mixed[1], callback_data=categories_mixed[1])
        button3 = types.InlineKeyboardButton(categories_mixed[2], callback_data=categories_mixed[2])
        text = 'Choose photo category!'
    markup = types.InlineKeyboardMarkup(row_width=2)
    # можно добавить методом row, но он будет игнорировать параметр row_width
    # и выведет в одной строке все добавленные через него кнопки
    markup.add(button1, button2, button3)
    await message.reply(text, reply_markup=markup, reply=False)
    # записываем кол-во обычных сообщений от каждого юзера
    users_stat_mes[message.from_user.id] = users_stat_mes.get(message.from_user.id, 0) + 1


@dp.message_handler()
async def inline_key_board_markup(message):
    '''
    main message handler with send button ReplyKeybodardMarkup1
    :param message:
    :return:
    '''
    # перемешиваем категории
    categories_mixed = r.sample(categories_lst, len(categories_lst))
    # Создаём объекты встроенной клавиатуры
    if message.from_user.language_code == 'ru':
        button1 = types.InlineKeyboardButton(
            categories_translate_dict[categories_mixed[0]],
            callback_data=categories_mixed[0]
        )
        button2 = types.InlineKeyboardButton(
            categories_translate_dict[categories_mixed[1]],
            callback_data=categories_mixed[1]
        )
        button3 = types.InlineKeyboardButton(
            categories_translate_dict[categories_mixed[2]],
            callback_data=categories_mixed[2]
        )
        text = 'Выбери категорию фото!'

        button_r = types.KeyboardButton("Показать категории")
        text_r = r'_\(доступна кнопка "Показать категории"\)_'
    else:
        button1 = types.InlineKeyboardButton(categories_mixed[0], callback_data=categories_mixed[0])
        button2 = types.InlineKeyboardButton(categories_mixed[1], callback_data=categories_mixed[1])
        button3 = types.InlineKeyboardButton(categories_mixed[2], callback_data=categories_mixed[2])
        text = 'Choose photo category!'
        button_r = types.KeyboardButton("Show categories")
        text_r = r'_\(the "Show categories" button is available\)_'
    markup = types.InlineKeyboardMarkup(row_width=2)
    # можно добавить методом row, но он будет игнорировать параметр row_width
    # и выведет в одной строке все добавленные через него кнопки
    markup.add(button1, button2, button3)
    await message.reply(text, reply_markup=markup, reply=False)
    markup_r = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup_r.add(button_r)
    await message.reply(text_r, reply_markup=markup_r, reply=False, parse_mode="MarkdownV2")
    # записываем кол-во обычных сообщений от каждого юзера
    users_stat_mes[message.from_user.id] = users_stat_mes.get(message.from_user.id, 0) + 1


@dp.edited_message_handler()
async def edited_message_handler_func(message):
    '''
    edited any message handler
    :param message:
    :return:
    '''
    await message.reply("Шалунишка, отредактировал сообщение?😁 \nЯ никому не расскажу 🙂")


@dp.callback_query_handler(lambda callback: callback.data == 'cats')
async def callback_button_cats(callback_query):
    '''
    InlineKeybodardMarkup button handler
    :param callback_query:
    :return:
    '''
    await bot.answer_callback_query(callback_query.id)
    random_pic_url = r.choice(list(container['cats']['urls']))
    pic_author = container['cats']['urls'][random_pic_url][1]  # !поменять в остальных обработчиках
    try:
        button1 = types.InlineKeyboardButton(
            '❤',
            callback_data=str(container['cats']['urls'][random_pic_url][2])
        )
    except IndexError:
        button1 = types.InlineKeyboardButton(
            '❤',
            callback_data="id_error"
        )
    markup = types.InlineKeyboardMarkup()
    markup.add(button1)
    await bot.send_photo(callback_query.from_user.id, random_pic_url, f'author: {pic_author}', reply_markup=markup)

    stat_writing(callback_query)


@dp.callback_query_handler(lambda callback: callback.data == 'dogs')
async def callback_button_dogs(callback_query):
    await bot.answer_callback_query(callback_query.id)
    random_pic_url = r.choice(list(container['dogs']['urls']))
    pic_author = container['dogs']['urls'][random_pic_url][1]
    try:
        button1 = types.InlineKeyboardButton(
            '❤', callback_data=str(container['dogs']['urls'][random_pic_url][2])
        )
    except IndexError:
        button1 = types.InlineKeyboardButton('❤', callback_data="id_error")
    markup = types.InlineKeyboardMarkup()
    markup.add(button1)
    await bot.send_photo(callback_query.from_user.id, random_pic_url, f'author: {pic_author}', reply_markup=markup)
    stat_writing(callback_query)


@dp.callback_query_handler(lambda callback: callback.data == 'nature')
async def callback_button_nature(callback_query):
    await bot.answer_callback_query(callback_query.id)
    random_pic_url = r.choice(list(container['nature']['urls']))
    pic_author = container['nature']['urls'][random_pic_url][1]
    try:
        button1 = types.InlineKeyboardButton(
            '❤', callback_data=str(container['nature']['urls'][random_pic_url][2])
        )
    except IndexError:
        button1 = types.InlineKeyboardButton('❤', callback_data="id_error")
    markup = types.InlineKeyboardMarkup()
    markup.add(button1)
    await bot.send_photo(callback_query.from_user.id, random_pic_url, f'author: {pic_author}', reply_markup=markup)
    stat_writing(callback_query)


@dp.callback_query_handler(lambda callback: callback.data == 'water')
async def callback_button_water(callback_query):
    await bot.answer_callback_query(callback_query.id)
    random_pic_url = r.choice(list(container['water']['urls']))
    pic_author = container['water']['urls'][random_pic_url][1]
    try:
        button1 = types.InlineKeyboardButton(
            '❤', callback_data=str(container['water']['urls'][random_pic_url][2])
        )
    except IndexError:
        button1 = types.InlineKeyboardButton('❤', callback_data="id_error")
    markup = types.InlineKeyboardMarkup()
    markup.add(button1)
    await bot.send_photo(callback_query.from_user.id, random_pic_url, f'author: {pic_author}', reply_markup=markup)
    stat_writing(callback_query)


@dp.callback_query_handler(lambda callback: callback.data == 'sea')
async def callback_button_sea(callback_query):
    await bot.answer_callback_query(callback_query.id)
    random_pic_url = r.choice(list(container['sea']['urls']))
    pic_author = container['sea']['urls'][random_pic_url][1]
    try:
        button1 = types.InlineKeyboardButton(
            '❤', callback_data=str(container['sea']['urls'][random_pic_url][2])
        )
    except IndexError:
        button1 = types.InlineKeyboardButton('❤', callback_data="id_error")
    markup = types.InlineKeyboardMarkup()
    markup.add(button1)
    await bot.send_photo(callback_query.from_user.id, random_pic_url, f'author: {pic_author}', reply_markup=markup)
    stat_writing(callback_query)


@dp.callback_query_handler(lambda callback: callback.data == 'food')
async def callback_button_food(callback_query):
    await bot.answer_callback_query(callback_query.id)
    random_pic_url = r.choice(list(container['food']['urls']))
    pic_author = container['food']['urls'][random_pic_url][1]
    try:
        button1 = types.InlineKeyboardButton(
            '❤', callback_data=str(container['food']['urls'][random_pic_url][2])
        )
    except IndexError:
        button1 = types.InlineKeyboardButton('❤', callback_data="id_error")
    markup = types.InlineKeyboardMarkup()
    markup.add(button1)
    await bot.send_photo(callback_query.from_user.id, random_pic_url, f'author: {pic_author}', reply_markup=markup)
    stat_writing(callback_query)


@dp.callback_query_handler(lambda callback: callback.data == 'coffee')
async def callback_button_coffee(callback_query):
    await bot.answer_callback_query(callback_query.id)
    random_pic_url = r.choice(list(container['coffee']['urls']))
    pic_author = container['coffee']['urls'][random_pic_url][1]
    try:
        button1 = types.InlineKeyboardButton(
            '❤', callback_data=str(container['coffee']['urls'][random_pic_url][2])
        )
    except IndexError:
        button1 = types.InlineKeyboardButton('❤', callback_data="id_error")
    markup = types.InlineKeyboardMarkup()
    markup.add(button1)
    await bot.send_photo(callback_query.from_user.id, random_pic_url, f'author: {pic_author}', reply_markup=markup)
    stat_writing(callback_query)


@dp.callback_query_handler(lambda callback: callback.data == 'sport')
async def callback_button_sport(callback_query):
    await bot.answer_callback_query(callback_query.id)
    random_pic_url = r.choice(list(container['sport']['urls']))
    pic_author = container['sport']['urls'][random_pic_url][1]
    try:
        button1 = types.InlineKeyboardButton(
            '❤', callback_data=str(container['sport']['urls'][random_pic_url][2])
        )
    except IndexError:
        button1 = types.InlineKeyboardButton('❤', callback_data="id_error")
    markup = types.InlineKeyboardMarkup()
    markup.add(button1)
    await bot.send_photo(callback_query.from_user.id, random_pic_url, f'author: {pic_author}', reply_markup=markup)
    stat_writing(callback_query)


@dp.callback_query_handler(lambda callback: callback.data == 'plane')
async def callback_button_plane(callback_query):
    await bot.answer_callback_query(callback_query.id)
    random_pic_url = r.choice(list(container['plane']['urls']))
    pic_author = container['plane']['urls'][random_pic_url][1]
    try:
        button1 = types.InlineKeyboardButton(
            '❤', callback_data=str(container['plane']['urls'][random_pic_url][2])
        )
    except IndexError:
        button1 = types.InlineKeyboardButton('❤', callback_data="id_error")
    markup = types.InlineKeyboardMarkup()
    markup.add(button1)
    await bot.send_photo(callback_query.from_user.id, random_pic_url, f'author: {pic_author}', reply_markup=markup)
    stat_writing(callback_query)


@dp.callback_query_handler(lambda callback: callback.data == 'mountains')
async def callback_button_mountains(callback_query):
    await bot.answer_callback_query(callback_query.id)
    random_pic_url = r.choice(list(container['mountains']['urls']))
    pic_author = container['mountains']['urls'][random_pic_url][1]
    try:
        button1 = types.InlineKeyboardButton(
            '❤', callback_data=str(container['mountains']['urls'][random_pic_url][2])
        )
    except IndexError:
        button1 = types.InlineKeyboardButton('❤', callback_data="id_error")
    markup = types.InlineKeyboardMarkup()
    markup.add(button1)
    await bot.send_photo(callback_query.from_user.id, random_pic_url, f'author: {pic_author}', reply_markup=markup)
    stat_writing(callback_query)


@dp.callback_query_handler(lambda callback: callback.data == 'mountain climbing')
async def callback_button_mountain_climbing(callback_query):
    await bot.answer_callback_query(callback_query.id)
    random_pic_url = r.choice(list(container['mountain climbing']['urls']))
    pic_author = container['mountain climbing']['urls'][random_pic_url][1]
    try:
        button1 = types.InlineKeyboardButton(
            '❤', callback_data=str(container['mountain climbing']['urls'][random_pic_url][2])
        )
    except IndexError:
        button1 = types.InlineKeyboardButton('❤', callback_data="id_error")
    markup = types.InlineKeyboardMarkup()
    markup.add(button1)
    await bot.send_photo(callback_query.from_user.id, random_pic_url, f'author: {pic_author}', reply_markup=markup)
    stat_writing(callback_query)


@dp.callback_query_handler(lambda callback: callback.data == 'travel')
async def callback_button_travel(callback_query):
    await bot.answer_callback_query(callback_query.id)
    random_pic_url = r.choice(list(container['travel']['urls']))
    pic_author = container['travel']['urls'][random_pic_url][1]
    try:
        button1 = types.InlineKeyboardButton(
            '❤', callback_data=str(container['travel']['urls'][random_pic_url][2])
        )
    except IndexError:
        button1 = types.InlineKeyboardButton('❤', callback_data="id_error")
    markup = types.InlineKeyboardMarkup()
    markup.add(button1)
    await bot.send_photo(callback_query.from_user.id, random_pic_url, f'author: {pic_author}', reply_markup=markup)
    stat_writing(callback_query)


@dp.callback_query_handler(lambda callback: callback.data == 'clouds')
async def callback_button_clouds(callback_query):
    await bot.answer_callback_query(callback_query.id)
    random_pic_url = r.choice(list(container['clouds']['urls']))
    pic_author = container['clouds']['urls'][random_pic_url][1]
    try:
        button1 = types.InlineKeyboardButton(
            '❤', callback_data=str(container['clouds']['urls'][random_pic_url][2])
        )
    except IndexError:
        button1 = types.InlineKeyboardButton('❤', callback_data="id_error")
    markup = types.InlineKeyboardMarkup()
    markup.add(button1)
    await bot.send_photo(callback_query.from_user.id, random_pic_url, f'author: {pic_author}', reply_markup=markup)
    stat_writing(callback_query)


@dp.callback_query_handler(lambda callback: callback.data == 'fire')
async def callback_button_fire(callback_query):
    await bot.answer_callback_query(callback_query.id)
    random_pic_url = r.choice(list(container['fire']['urls']))
    pic_author = container['fire']['urls'][random_pic_url][1]
    try:
        button1 = types.InlineKeyboardButton(
            '❤', callback_data=str(container['fire']['urls'][random_pic_url][2])
        )
    except IndexError:
        button1 = types.InlineKeyboardButton('❤', callback_data="id_error")
    markup = types.InlineKeyboardMarkup()
    markup.add(button1)
    await bot.send_photo(callback_query.from_user.id, random_pic_url, f'author: {pic_author}', reply_markup=markup)
    stat_writing(callback_query)


@dp.callback_query_handler(lambda callback: callback.data == 'friends')
async def callback_button_friends(callback_query):
    await bot.answer_callback_query(callback_query.id)
    random_pic_url = r.choice(list(container['friends']['urls']))
    pic_author = container['friends']['urls'][random_pic_url][1]
    try:
        button1 = types.InlineKeyboardButton(
            '❤', callback_data=str(container['friends']['urls'][random_pic_url][2])
        )
    except IndexError:
        button1 = types.InlineKeyboardButton('❤', callback_data="id_error")
    markup = types.InlineKeyboardMarkup()
    markup.add(button1)
    await bot.send_photo(callback_query.from_user.id, random_pic_url, f'author: {pic_author}', reply_markup=markup)
    stat_writing(callback_query)


@dp.callback_query_handler(lambda callback: callback.data == 'forest')
async def callback_button_forest(callback_query):
    await bot.answer_callback_query(callback_query.id)
    random_pic_url = r.choice(list(container['forest']['urls']))
    pic_author = container['forest']['urls'][random_pic_url][1]
    try:
        button1 = types.InlineKeyboardButton(
            '❤', callback_data=str(container['forest']['urls'][random_pic_url][2])
        )
    except IndexError:
        button1 = types.InlineKeyboardButton('❤', callback_data="id_error")
    markup = types.InlineKeyboardMarkup()
    markup.add(button1)
    await bot.send_photo(callback_query.from_user.id, random_pic_url, f'author: {pic_author}', reply_markup=markup)
    stat_writing(callback_query)


@dp.callback_query_handler(lambda callback: callback.data == 'sun')
async def callback_button_sun(callback_query):
    await bot.answer_callback_query(callback_query.id)
    random_pic_url = r.choice(list(container['sun']['urls']))
    pic_author = container['sun']['urls'][random_pic_url][1]
    try:
        button1 = types.InlineKeyboardButton(
            '❤', callback_data=str(container['sun']['urls'][random_pic_url][2])
        )
    except IndexError:
        button1 = types.InlineKeyboardButton('❤', callback_data="id_error")
    markup = types.InlineKeyboardMarkup()
    markup.add(button1)
    await bot.send_photo(callback_query.from_user.id, random_pic_url, f'author: {pic_author}', reply_markup=markup)
    stat_writing(callback_query)


@dp.callback_query_handler(lambda callback: callback.data == 'wild animals')
async def callback_button_wild_animals(callback_query):
    await bot.answer_callback_query(callback_query.id)
    random_pic_url = r.choice(list(container['wild animals']['urls']))
    pic_author = container['wild animals']['urls'][random_pic_url][1]
    try:
        button1 = types.InlineKeyboardButton(
            '❤', callback_data=str(container['wild animals']['urls'][random_pic_url][2])
        )
    except IndexError:
        button1 = types.InlineKeyboardButton('❤', callback_data="id_error")
    markup = types.InlineKeyboardMarkup()
    markup.add(button1)
    await bot.send_photo(callback_query.from_user.id, random_pic_url, f'author: {pic_author}', reply_markup=markup)
    stat_writing(callback_query)


@dp.callback_query_handler(lambda callback: callback.data == 'smile')
async def callback_button_smile(callback_query):
    await bot.answer_callback_query(callback_query.id)
    random_pic_url = r.choice(list(container['smile']['urls']))
    pic_author = container['smile']['urls'][random_pic_url][1]
    try:
        button1 = types.InlineKeyboardButton(
            '❤', callback_data=str(container['smile']['urls'][random_pic_url][2])
        )
    except IndexError:
        button1 = types.InlineKeyboardButton('❤', callback_data="id_error")
    markup = types.InlineKeyboardMarkup()
    markup.add(button1)
    await bot.send_photo(callback_query.from_user.id, random_pic_url, f'author: {pic_author}', reply_markup=markup)
    stat_writing(callback_query)


@dp.callback_query_handler(lambda callback: callback.data == 'baby')
async def callback_button_baby(callback_query):
    await bot.answer_callback_query(callback_query.id)
    random_pic_url = r.choice(list(container['baby']['urls']))
    pic_author = container['baby']['urls'][random_pic_url][1]
    try:
        button1 = types.InlineKeyboardButton(
            '❤', callback_data=str(container['baby']['urls'][random_pic_url][2])
        )
    except IndexError:
        button1 = types.InlineKeyboardButton('❤', callback_data="id_error")
    markup = types.InlineKeyboardMarkup()
    markup.add(button1)
    await bot.send_photo(callback_query.from_user.id, random_pic_url, f'author: {pic_author}', reply_markup=markup)
    stat_writing(callback_query)


@dp.callback_query_handler(lambda callback: callback.data == 'religion')
async def callback_button_religion(callback_query):
    await bot.answer_callback_query(callback_query.id)
    random_pic_url = r.choice(list(container['religion']['urls']))
    pic_author = container['religion']['urls'][random_pic_url][1]
    try:
        button1 = types.InlineKeyboardButton(
            '❤', callback_data=str(container['religion']['urls'][random_pic_url][2])
        )
    except IndexError:
        button1 = types.InlineKeyboardButton('❤', callback_data="id_error")
    markup = types.InlineKeyboardMarkup()
    markup.add(button1)
    await bot.send_photo(callback_query.from_user.id, random_pic_url, f'author: {pic_author}', reply_markup=markup)
    stat_writing(callback_query)


@dp.callback_query_handler()
async def callback_button_like(callback_query):
    '''
    likes handler
    :param callback_query:
    :return:
    '''
    await bot.answer_callback_query(callback_query.id)
    # file_id = callback_query.message.photo[3].file_id
    photo_id = callback_query.data
    if likes_photo_dct.get(photo_id):
        likes_photo_dct[photo_id][1] += 1
    else:
        likes_photo_dct[photo_id] = [callback_query.message.caption, 1]

    try:
        button1 = types.InlineKeyboardButton(
            '💓💓💓',
            db.select_simple("container", ["url_original"], {"id": int(callback_query.data)})[0][0]
        )
    except pymysql.Error as err:  # ожидаю здесь ошибки соединения с базой данных или
        print("!!Data Base ERROR!!:\n", f"{err.__class__}: ", err)
        button1 = types.InlineKeyboardButton(
            '💓💓💓',
            "https://images.pexels.com/photos/1003993/pexels-photo-1003993.jpeg"
        )

    markup = types.InlineKeyboardMarkup(resize_keyboard=True)
    markup.add(button1)
    await bot.edit_message_reply_markup(
        callback_query.from_user.id,
        callback_query.message.message_id,
        reply_markup=markup
    )


async def db_statistics_update() -> None:
    """
    write in db and clear 4 dicts:
    users_stat, users_stat_mes, categories_stat, time_stat
    """
    while True:
        await asyncio.sleep(60 * 59)  # для heroku обновляем раз в 59 мин
        print('db_statistics_update!')

        await insert_update_db("stat_users", users_stat, ["user_id", "requests_number"])
        users_stat.clear()
        await insert_update_db("stat_users", users_stat_mes, ["user_id", "messages_number"])
        users_stat_mes.clear()
        await insert_update_db("stat_categories", categories_stat, ["category", "requests_number"])
        categories_stat.clear()
        await insert_update_db("stat_time", time_stat, ["time", "requests_number"])
        time_stat.clear()
        # db likes_photo update
        for photo_id, value in likes_photo_dct.items():
            # form a local dictionary for transferring it to insert_one
            input_dct = dict()
            input_dct["photo_id"] = photo_id
            input_dct["author"] = value[0]
            input_dct["likes_number"] = value[1]
            if db.insert_one("likes_photo", input_dct) is not None:
                n = db.select_simple(
                    "likes_photo",
                    ["likes_number"],
                    {"photo_id": photo_id}
                )[0][0]
                db.update_simple_one(
                    "likes_photo",
                    "likes_number",
                    n + input_dct["likes_number"],
                    {"photo_id": photo_id}
                )
        likes_photo_dct.clear()


async def container_update_in_aiogram_eventloop() -> None:
    '''
    "container" update
    :return:
    '''
    while True:
        await asyncio.sleep(60 * 60 * 12)  # normal: update every 12 hours
        try:
            await main_container_update(3)  # normal value: 3
        except CategoryError as err:
            print(err.__class__, err)
            main_container_filling_from_db(1)
        test_func()


async def time_sending_for_users():
    '''
    send 3 random photo for each user (recommend once in 24 hours)
    :return:
    '''
    while True:
        now_time = datetime.now(tz=timezone(timedelta(hours=3))).time()
        need_time = time(hour=12, minute=0, second=0)  # 12:00:00 optimal
        # need_time = datetime.now(tz=timezone(timedelta(hours=3, minutes=1))).time()  # for tests
        sleep_t = (
                (((need_time.hour - now_time.hour) + 24) % 24) * 3600 +
                (need_time.minute - now_time.minute) * 60 +
                (need_time.second - now_time.second)
        )
        if sleep_t <= 0:
            sleep_t += 24 * 3600

        await asyncio.sleep(sleep_t)
        print('time_sending_for_users!')

        data = db.select_simple("users", ["id"])

        def get_media_obj(categories: list) -> types.MediaGroup:
            photos = list()
            for i in range(len(categories)):
                photos.append([r.choice(list(container[categories[i]]["urls"]))])
                photos[i].append(container[categories[i]]["urls"][photos[i][0]][1])
            media = types.MediaGroup()
            for lst in photos:
                media.attach_photo(lst[0], lst[1])
            return media

        # restriction api telegram-bot: 30 mes/s
        # for every 10 users generate unique photo-selection
        categories = ['cats', 'dogs', "nature"]
        # categories = r.sample(categories_lst, k=3)
        media = get_media_obj(categories)
        count = 0
        for element in data:
            if count % 10 == 0 and count != 0:
                media = get_media_obj(categories)
                await asyncio.sleep(1)

            await bot.send_media_group(element[0], media)
            count += 1


if __name__ == '__main__':
    try:
        asyncio.run(main_for_first_data_filling(2))  # 3
        print("main_for_first_data_filling completed!")
    except CategoryError as err:
        print(err.__class__, err)
        main_container_filling_from_db_first(1)

    # add periodic update func's in aiogram event loop
    dp.loop.create_task(db_statistics_update())
    dp.loop.create_task(time_sending_for_users())
    # Start bot in long-polling mode
    executor.start_polling(dp)
