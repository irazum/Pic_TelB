'''
~~!!uploader urls from API-pexels.com!!~~
'''
import asyncio
import aiohttp
from async_MySQL_pic_bot_db_func import *


categories_lst = [
    'cats', 'dogs', 'nature', 'water', 'sea', 'food', 'coffee',
    'sport', 'plane', 'mountains', 'mountain climbing', 'travel',
    'clouds', 'fire', 'friends', 'forest', 'sun', 'wild animals',
    'smile', 'baby', 'religion'
]

# For debugging
# categories_lst = ['cats', 'dogs', "sea"]

categories_translate_dict = {
    'cats': 'котики', 'dogs': 'собаки', 'nature': 'природа', 'water': 'водичка',
    'sea': 'море', 'food': 'еда', 'coffee': 'кофе', 'sport': 'спорт',
    'healthy': 'здоровье', 'green': 'зелень', 'relax': 'релакс', 'plane': 'самолёт',
    'mountains': 'горы', 'mountain climbing': 'люди и горы', 'travel': 'путешествия',
    'creative': 'креатив', 'clouds': 'облака', 'fire': 'пламя', 'friends': 'друзья',
    'forest': 'лес', 'sun': 'солнце', 'night': 'ночь', 'wild animals': 'дикие животные',
    'smile': 'улыбки', 'crowd': 'Много людей', 'baby': 'дети', 'girl': 'девушка',
    'girls': 'девушки', 'naked man': 'парни', 'religion': 'религии'
}

container = {}
'''
self.container = {
    'cats': {'total_results': num, 'urls': {
                'https//...jpg': ['https//...jpg', 'photographer', id], 
                'https//...jpg': ['https//...jpg', 'photographer', id]
            }
    },
    'dogs': {'total_results': num, 'urls': {'https//...jpg': ['https//...jpg', 'photographer', id]}}
}
'''


class CategoryError(BaseException):
    pass


class AdditionalFuncs:
    def random_page_choice(self, pages, iter_number, category):
        """
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

    async def db_and_local_dct_update(self, category: str, urls_dct: dict, db: AioDatabase):
        '''
        loading urls from urls_dct in date base and then
        update urls_dct with urls id
        :param category:
        :param urls_dct:
        :return:
        '''
        try:
            # upload urls in db
            await db.url_db_loader(category, urls_dct)  # 1) Сделать эту функцию асинхронной
            # add id-photo from db in urls_dct
            for url in urls_dct:
                id_data = await db.select_simple("container", ["id"], {"url": url})
                urls_dct[url].append(id_data[0][0])
        except aiomysql.Error as err:
            print("!!Data Base ERROR!!:\n", f"{err.__class__}: ", err)

    def test_func(self):
        '''
        debugging func, print urls number in "container"-dict
        and writing "container" in file for checking
        :return: None
        '''
        for i in container.values():
            print(len(i['urls']), end=' ')
        print()
        # print(container)
        # with open('test_pic.txt', 'w', encoding='utf-8') as file1:
        #     file1.write(str(container))


class GetFunc:
    async def init_pictures_url(self, session, category, page):
        """
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


class LoadersFuncs(GetFunc, AdditionalFuncs):
    async def first_container_filling(self, session, category):
        """
        writings urls in container and db
        :param session:
        :param category:
        :return: None
        """
        # writing photo urls, it authors and total number of pictures
        # in each category in container with first page pexels api
        data = await self.init_pictures_url(session, category, 1)
        total_results = data['total_results']
        container[category] = {'total_results': total_results, 'urls': dict()}

        # # loading categories from categories_lst in db - !!use 1 time in test running only with new db!!
        # for title in categories_lst:
        #     await db.insert_one("categories", {"category": f'{title}'})

    async def container_filling(self, session, category, iter_number):
        """
        writings and then adds urls in container and db
        :param session:
        :param category:
        :param iter_number:
        :return: None
        """
        await self.first_container_filling(session, category)

        pages = container[category]['total_results'] // 80
        random_pages = self.random_page_choice(pages, iter_number, category)
        for i in range(iter_number):
            data = await self.init_pictures_url(session, category, random_pages[i])
            urls_dct = {}
            for dct in data['photos']:
                urls_dct[dct['src']['large2x']] = [dct['src']['original'], dct['photographer']]

            await self.db_and_local_dct_update(category, urls_dct, db)
            container[category]['urls'].update(urls_dct)

    async def container_add(self, session, category, iter_number):
        """
        adds random urls of need category in "container"
        :param session:
        :param category:
        :param iter_number:
        :return: None
        """
        pages = container[category]['total_results'] // 80
        random_pages = self.random_page_choice(pages, iter_number, category)

        for i in range(iter_number):
            data = await self.init_pictures_url(session, category, random_pages[i])
            urls_dct = {}
            for dct in data['photos']:
                urls_dct[dct['src']['large2x']] = [dct['src']['original'], dct['photographer']]

            await self.db_and_local_dct_update(category, urls_dct, db)

            container[category]['urls'].update(urls_dct)


class FirstLoader(LoadersFuncs):  # rename to FirstLoader
    async def main(self, iter_number):
        tasks = []
        async with aiohttp.ClientSession() as session:
            # creating task-objects for each category of container_filling
            for category in categories_lst:
                task = asyncio.create_task(self.container_filling(session, category, iter_number))
                tasks.append(task)
            # feed coroutines (tasks) to the .gather method for added them in event loop
            await asyncio.gather(*tasks)


class FirstLoaderFromDb(LoadersFuncs):  # rename to FirstLoaderFromDb
    def main(self, iter_number, db: AioDatabase):
        '''
            upload random photo from db in case,
            when bot starts and we get of special error on API_pexels
            (the requested category is less photo than we need)
            :param db: Database object
            :param iter_number: loading iterations number
            :return: None
            '''
        for category in categories_lst:
            for i in range(iter_number):
                urls_dct = db.select_url(category)
                container[category] = {'total_results': 100, 'urls': urls_dct}


class UpdateLoader(LoadersFuncs):  # rename to UpdateLoader
    async def main(self, iter_number):
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
                    task = asyncio.create_task(self.container_add(session, category, iter_number))
                else:
                    task = asyncio.create_task(self.container_filling(session, category, iter_number - 1))
                tasks.append(task)
            await asyncio.gather(*tasks)


class UpdateLoaderFromDb:  # rename to UpdateLoaderFromDb
    def main(self, iter_number, db: AioDatabase):
        '''
            upload random photo from db in case,
            when container updating and we get of special error on API_pexels
            (the requested category is less photo than we need)
            :param db: Database object
            :param iter_number: loading iterations number
            :return: None
            '''
        for category in categories_lst:
            for i in range(iter_number):
                urls_dct = db.select_url(category)
                container[category]['urls'].update(urls_dct)


