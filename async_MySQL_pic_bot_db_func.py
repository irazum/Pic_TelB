import aiomysql
import logging
import random as r
from os import environ


class Config:
    def __init__(self):
        self.host = environ['host']
        self.user = environ['user']
        self.password = environ['password']
        self.db = environ['db']

        self.telegram_bot_token = environ['telegram_bot_token']
        self.pixels_api_token = environ['pixels_api_token']

        self.statistics_user_1 = environ['statistics_user_1']
        self.statistics_categories_1 = environ['statistics_categories_1']
        self.statistics_time_1 = environ['statistics_time_1']
        self.statistics_user_2 = environ['statistics_user_2']
        self.statistics_categories_2 = environ['statistics_categories_2']
        self.statistics_time_2 = environ['statistics_time_2']
        self.statistics_likes = environ['statistics_likes']


class AioDatabase:
    def __init__(self, config: Config):
        self.host = config.host
        self.user = config.user
        self.password = config.password
        self.db = config.db

    async def __open_conn(self):
        conn = await aiomysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            db=self.db,
            port=3306,
            charset='utf8mb4',
            connect_timeout=3600*4
            )
        return conn


    async def insert_one(self, table: str, column_value: dict):
        '''
        universal pymysql single row insertion
        :param table: name of table
        :param column_value: dict {column1_name: value1, column2_name: value2, ..}
        :return: None or exception-string
        '''
        try:
            conn = await self.__open_conn()
            async with conn.cursor() as cur:
                columns = ','.join(column_value.keys())
                placeholders = ', '.join(['%s' for i in range(len(column_value))])
                values = tuple(column_value.values())
                await cur.execute(
                    f'insert into {table}'
                    f'({columns})'
                    f'values'
                    f'({placeholders});',
                    values)
                await conn.commit()
            conn.close()
        # table constraint exception handler
        except aiomysql.IntegrityError as exc:
            return str(exc)


    async def select_simple(self, table: str, columns: list, conditions=None, operator='and'):
        '''
        universal pymysql select func without subquery and join
        :param table: table name
        :param columns: list of selected columns names
        :param conditions: dict of conditions for
            where-sql-operator {column1_name: value1, column2_name: value2, ..}
        :param operator: and, or
        :return:
        '''
        conn = await self.__open_conn()
        async with conn.cursor() as cur:
            if conditions is None:
                conditions = {}
            columns_str = ','.join(columns)
            condition_str_lst = []
            values = []
            for key, val in conditions.items():
                condition_str_lst.append(f"{key}=%s")
                values.append(val)
            values = tuple(values)
            if len(condition_str_lst) > 0:
                condition_str_lst[0] = f'where {condition_str_lst[0]}'
            condition_str = f' {operator} '.join(condition_str_lst)

            await cur.execute(
                f"select {columns_str} from {table} "
                f"{condition_str};",
                values
            )
            data = await cur.fetchall()
        conn.close()
        return data


    async def select_inner_join_simple(self, table1: str, table2: str, inner: tuple, columns: list):
        """
        universal pymysql select select join func
        :param table1: table1 name
        :param table2: table2 name
        :param inner: tuple of column which must match (table1_column, table2_column)
        :param columns: need columns in result
        :return:
        """
        conn = await self.__open_conn()
        async with conn.cursor() as cur:
            columns_str = ','.join(columns)
            await cur.execute(
                f"select {columns_str} from {table1} as t1 "
                f"inner join {table2} as t2 "
                f"on t1.{inner[0]} = t2.{inner[1]};"
            )
            data = await cur.fetchall()
        conn.close()
        return data


    async def update_simple_one(self, table: str, column: str, value, conditions: dict, operator='and'):
        """
        universal pymysql update func
        :param table: table name
        :param column: column name
        :param value: insert value
        :param conditions: conditions: dict of conditions for
            where-sql-operator {column1_name: value1, column2_name: value2, ..}
        :param operator: and, or
        :return:
        """
        conn = await self.__open_conn()
        async with conn.cursor() as cur:
            condition_str_lst = []
            values = [value]
            for key, val in conditions.items():
                condition_str_lst.append(f"{key}=%s")
                values.append(val)
            values = tuple(values)
            if len(condition_str_lst) > 0:
                condition_str_lst[0] = f'where {condition_str_lst[0]}'
            condition_str = f' {operator} '.join(condition_str_lst)

            await cur.execute(
                f"update {table} set {column}=%s "
                f"{condition_str};",
                values
            )
            await conn.commit()
        conn.close()




    async def url_db_loader(self, category: str, dct: dict):
        '''
        special pymysql function for writing urls in database after urls loading
        :param category: name of photos category
        :param dct: service dict initializing function
        :return: None
        '''
        conn = await self.__open_conn()
        async with conn.cursor() as cur:
            for key, value in dct.items():
                try:
                    await cur.execute(
                        f"insert into container values "
                        f"("
                        f"Null, %s, %s, %s, (select category_id from categories where category = %s) "
                        f");",
                        (key, value[0], value[1], category)
                    )
                except aiomysql.IntegrityError:
                    pass
            await conn.commit()
        conn.close()


    async def select_url(self, category: str):
        """
        :param category: name of category
        :return: dict with 80 urls and their captions or less
        """
        conn = await self.__open_conn()
        async with conn.cursor() as cur:
            await cur.execute(
                f'select url, url_original, photographer, id '
                f'from container as con '
                f'inner join categories as cat '
                f'on con.category_id = cat.category_id '
                f'where category = %s;',
                (category,)
            )
            data = await cur.fetchall()
            if len(data) > 80:
                data = r.sample(data, 80)
            dct = {}
            for element in data:
                dct[element[0]] = [element[1], element[2], element[3]]
        conn.close()
        return dct


config = Config()
db = AioDatabase(config)


if __name__ == '__main__':
    pass
