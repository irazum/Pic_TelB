categories_lst = [
    'cats', 'dogs', 'nature', 'water', 'sea', 'food', 'coffee', 'sport',
    'plane', 'mountains', 'mountain climbing', 'travel', 'clouds', 'fire',
    'friends', 'forest', 'sun', 'wild animals', 'smile', 'baby',
    'religion'
]


with open('callback_code.txt', 'w', encoding='utf-8') as file1:
    pic_author = '{pic_author}'
    for category in categories_lst:
        category_for_func = category
        if ' ' in category:
            category_for_func = f"{category.split()[0]}_{category.split()[1]}"
        s = f'''
@dp.callback_query_handler(lambda callback: callback.data == '{category}')
async def callback_button_{category_for_func}(callback_query):
    await bot.answer_callback_query(callback_query.id)
    random_pic_url = r.choice(list(container['{category}']['urls']))
    pic_author = container['{category}']['urls'][random_pic_url][1]
    try:
        button1 = types.InlineKeyboardButton(
            '❤', callback_data=str(container['{category}']['urls'][random_pic_url][2]) 
        )
    except IndexError:
        button1 = types.InlineKeyboardButton('❤', callback_data="id_error")
    markup = types.InlineKeyboardMarkup()
    markup.add(button1)
    await bot.send_photo(callback_query.from_user.id, random_pic_url, f'author: {pic_author}', reply_markup=markup)
    stat_writing(callback_query)

        '''

        file1.write(s)
