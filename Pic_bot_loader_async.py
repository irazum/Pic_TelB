'''
~~!!uploader urls from API-pexels.com!!~~
'''
import asyncio
import aiohttp
from mod_MySQL_pic_bot_db_func import *

categories_lst = [
    'cats', 'dogs', 'nature', 'water', 'sea', 'food', 'coffee', 'sport',
    'plane', 'mountains', 'mountain climbing', 'travel', 'clouds', 'fire',
    'friends', 'forest', 'sun', 'wild animals', 'smile', 'baby',
    'religion'
]
# For debugging
# categories_lst = ['cats', 'dogs', "nature", "sea"]

categories_translate_dict = {
    'cats': 'котики', 'dogs': 'собаки', 'nature': 'природа', 'water': 'водичка',
    'sea': 'море', 'food': 'еда', 'coffee': 'кофе', 'sport': 'спорт',
    'healthy': 'здоровье', 'green': 'зелень', 'relax': 'релакс', 'plane': 'самолёт',
    'mountains': 'горы', 'mountain climbing': 'люди и горы', 'travel': 'путешествия', 'creative': 'креатив',
    'clouds': 'облака', 'fire': 'пламя', 'friends': 'друзья', 'forest': 'лес',
    'sun': 'солнце', 'night': 'ночь', 'wild animals': 'дикие животные', 'smile': 'улыбки',
    'crowd': 'Много людей', 'baby': 'дети', 'girl': 'девушка', 'girls': 'девушки',
    'naked man': 'парни', 'religion': 'религии'
}

'''
container = {
    'cats': {'total_results': num, 'urls': {
                'https//...jpg': ['https//...jpg', 'photographer', id], 
                'https//...jpg': ['https//...jpg', 'photographer', id]
            }
    },
    'dogs': {'total_results': num, 'urls': {'https//...jpg': ['https//...jpg', 'photographer', id]}}
}
'''
container = {}

admin_id = {}  # {'admin_id': id}


#
class CategoryError(BaseException):
    pass


def random_page_choice(pages, iter_number, category):
    """
    Used in secondary functions
    :param pages:
    :param iter_number:
    :param category:
    :return: list of random numbers (pages), starting from 1 in quantity iter_number
    """
    # checking the sufficiency of the number of category pages
    if pages <= iter_number:
        raise CategoryError(f'{category} have not {iter_number + 1} pages '
                            f'({(iter_number + 1) * 80} pictures)' 
                            f', please delete this category')
    random_lst = [1]
    rand = 1
    for i in range(iter_number):
        while rand in random_lst:
            rand = r.randrange(2, pages + 1)
        random_lst.append(rand)
    return random_lst[1::]


def db_and_local_dct_update(category: str, urls_dct: dict):
    '''
    Used in secondary functions;
    loading urls from urls_dct in date base and then
    update urls_dct with urls id
    :param category:
    :param urls_dct:
    :return:
    '''
    try:
        # upload urls in db
        db.url_db_loader(category, urls_dct)
        # add id-photo from db in urls_dct
        for url in urls_dct:
            urls_dct[url].append(
                db.select_simple("container", ["id"], {"url": url})[0][0]
            )
    except pymysql.Error as err:
        print("!!Data Base ERROR!!:\n", f"{err.__class__}: ", err)


async def init_pictures_url(session, category, page):
    """
    Used in secondary functions;
    use asynchronous http-get requests
    :param session: aiohttp.ClientSession()
    :param category: photo category
    :param page: random page for get-request
    :return: dict of photos data
    По сути только при выполнении этой функции созданные таски будут конкурировать,
    только get-запросы в нашем загрузчике будут исполняться конкуренотно(асинхронно)
    """
    url = f'https://api.pexels.com/v1/search'
    params = {'query': category, 'per_page': 80, 'page': page}
    headers = {'Authorization': config.pixels_api_token}
    # make get-request to aiohttp.ClientSession() object
    async with session.get(url, params=params, headers=headers) as response:
        data = await response.json()
    return data


async def first_container_filling(session, category):
    """
    Used in secondary functions;
    writings urls in container and db
    :param session:
    :param category:
    :return: None
    """
    # writing photo urls, it authors and total number of pictures
    # in each category in container with first page pexels api
    data = await init_pictures_url(session, category, 1)
    total_results = data['total_results']
    urls_dct = {}
    for dct in data['photos']:
        urls_dct[dct['src']['large2x']] = [dct['src']['original'], dct['photographer']]
    # loading categories from categories_lst in db
    for title in categories_lst:
        db.insert_one("categories", {"category": f'{title}'})
    # loading urls_dct in db and update urls_dct
    db_and_local_dct_update(category, urls_dct)

    container[category] = {'total_results': total_results, 'urls': urls_dct}


async def container_filling(session, category, iter_number):
    """
    Used in main-functions;
    writings and then adds urls in container and db
    :param session:
    :param category:
    :param iter_number:
    :return: None
    """
    await first_container_filling(session, category)
    pages = container[category]['total_results'] // 80
    random_pages = random_page_choice(pages, iter_number, category)

    for i in range(iter_number):
        data = await init_pictures_url(session, category, random_pages[i])
        urls_dct = {}
        for dct in data['photos']:
            urls_dct[dct['src']['large2x']] = [dct['src']['original'], dct['photographer']]

        db_and_local_dct_update(category, urls_dct)

        container[category]['urls'].update(urls_dct)


async def container_add(session, category, iter_number):
    """
    used in main-functions;
    adds random urls of need category in "container"
    :param session:
    :param category:
    :param iter_number:
    :return: None
    """
    pages = container[category]['total_results'] // 80
    random_pages = random_page_choice(pages, iter_number, category)

    for i in range(iter_number):
        data = await init_pictures_url(session, category, random_pages[i])
        urls_dct = {}
        for dct in data['photos']:
            urls_dct[dct['src']['large2x']] = [dct['src']['original'], dct['photographer']]

        db_and_local_dct_update(category, urls_dct)

        container[category]['urls'].update(urls_dct)


async def main_for_first_data_filling(iter_number):
    '''
    writing urls in "container"
    :param iter_number:
    :return:
    '''
    tasks = []
    async with aiohttp.ClientSession() as session:
        # creating task-objects for each category of container_filling
        for category in categories_lst:
            task = asyncio.create_task(container_filling(session, category, iter_number - 1))
            tasks.append(task)
        # feed coroutines (tasks) to the .gather method for added them in event loop
        await asyncio.gather(*tasks)


async def main_container_update(iter_number):
    '''
    adds urls in container or rewriting it
    depending on the condition of the "container"-dict
    :param iter_number:
    :return:
    '''
    tasks = []
    async with aiohttp.ClientSession() as session:
        for category in categories_lst:
            number_of_pic = container[category]['total_results']
            number_of_urls = len(container[category]['urls'])
            if number_of_pic // 2 >= number_of_urls and number_of_urls <= 1000:
                task = asyncio.create_task(container_add(session, category, iter_number))
            else:
                task = asyncio.create_task(container_filling(session, category, iter_number - 1))
            tasks.append(task)
        await asyncio.gather(*tasks)


def main_container_filling_from_db_first(iter_number):
    '''
    upload random photo from db in case,
    when bot starts and we get of special error on API_pexels
    (the requested category is less photo than we need)
    :param iter_number: loading iterations number
    :return: None
    '''
    for category in categories_lst:
        for i in range(iter_number):
            urls_dct = db.select_url(category)
            container[category] = {'total_results': 100, 'urls': urls_dct}


def main_container_filling_from_db(iter_number):
    '''
    upload random photo from db in case,
    when container updating and we get of special error on API_pexels
    (the requested category is less photo than we need)
    :param iter_number: loading iterations number
    :return: None
    '''
    for category in categories_lst:
        for i in range(iter_number):
            urls_dct = db.select_url(category)
            container[category]['urls'].update(urls_dct)


def test_func():
    '''
    debugging func, print urls number in "container"-dict
    and writing "container" in file for checking
    :return: None
    '''
    for i in container.values():
        print(len(i['urls']))
    print(container)
    with open('test_pic.txt', 'w', encoding='utf-8') as file1:
        file1.write(str(container))
