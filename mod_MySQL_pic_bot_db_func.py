import pymysql
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


class Database:
    def __init__(self, config):
        self.host = config.host
        self.user = config.user
        self.password = config.password
        self.db = config.db
        self.conn = None

    def _open_conn_(self):
        try:
            if self.conn is None:
                self.conn = pymysql.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    db=self.db,
                    port=3306,
                    charset='utf8mb4',
                    connect_timeout=3600*4
                )
        except pymysql.Error as err:
            print("!!Data Base Connection ERROR!!:\n", f"{err.__class__}: ", err)

    def insert_one(self, table: str, column_value: dict):
        '''
        universal pymysql single row insertion
        :param table: name of table
        :param column_value: dict {column1_name: value1, column2_name: value2, ..}
        :return: None or exception-string
        '''
        self._open_conn_()
        try:
            with self.conn.cursor() as cur:
                columns = ','.join(column_value.keys())
                placeholders = ', '.join(['%s' for i in range(len(column_value))])
                values = tuple(column_value.values())
                cur.execute(
                    f'insert into {table}'
                    f'({columns})'
                    f'values'
                    f'({placeholders});',
                    values)
                self.conn.commit()
        # table constraint exception handler
        except pymysql.IntegrityError as exc:
            return str(exc)
        except pymysql.Error as err:
            print("!!Data Base ERROR!!:\n", f"{err.__class__}: ", err)
        except AttributeError as err:
            print("!!Data Base Functions ERROR!!:\n", f"{err.__class__}: ", err)
        # close connection
        finally:
            if self.conn:
                self.conn.close()
                self.conn = None

    def select_simple(self, table: str, columns: list, conditions=None, operator='and'):
        '''
        universal pymysql select func without subquery and join
        :param table: table name
        :param columns: list of selected columns names
        :param conditions: dict of conditions for
            where-sql-operator {column1_name: value1, column2_name: value2, ..}
        :param operator: and, or
        :return:
        '''
        self._open_conn_()
        try:
            with self.conn.cursor() as cur:
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

                cur.execute(
                    f"select {columns_str} from {table} "
                    f"{condition_str};",
                    values
                )
                return cur.fetchall()
        except pymysql.Error as err:
            print("!!Data Base ERROR!!:\n", f"{err.__class__}: ", err)
        except AttributeError as err:
            print("!!Data Base Functions ERROR!!:\n", f"{err.__class__}: ", err)
        finally:
            if self.conn:
                self.conn.close()
                self.conn = None

    def select_inner_join_simple(self, table1: str, table2: str, inner: tuple, columns: list):
        """
        universal pymysql select select join func
        :param table1: table1 name
        :param table2: table2 name
        :param inner: tuple of column which must match (table1_column, table2_column)
        :param columns: need columns in result
        :return:
        """
        self._open_conn_()
        try:
            with self.conn.cursor() as cur:
                columns_str = ','.join(columns)
                cur.execute(
                    f"select {columns_str} from {table1} as t1"
                    f"inner join {table2} as t2"
                    f"on t1.{inner[0]} = t2.{inner[1]};"
                )
                return cur.fetchall()
        except pymysql.Error as err:
            print("!!Data Base ERROR!!:\n", f"{err.__class__}: ", err)
        except AttributeError as err:
            print("!!Data Base Functions ERROR!!:\n", f"{err.__class__}: ", err)
        finally:
            if self.conn:
                self.conn.close()
                self.conn = None

    def update_simple_one(self, table: str, column: str, value, conditions: dict, operator='and'):
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
        self._open_conn_()
        try:
            with self.conn.cursor() as cur:
                condition_str_lst = []
                values = [value]
                for key, val in conditions.items():
                    condition_str_lst.append(f"{key}=%s")
                    values.append(val)
                values = tuple(values)
                if len(condition_str_lst) > 0:
                    condition_str_lst[0] = f'where {condition_str_lst[0]}'
                condition_str = f' {operator} '.join(condition_str_lst)

                cur.execute(
                    f"update {table} set {column}=%s "
                    f"{condition_str};",
                    values
                )
                self.conn.commit()
        except pymysql.Error as err:
            print("!!Data Base ERROR!!:\n", f"{err.__class__}: ", err)
        except AttributeError as err:
            print("!!Data Base Functions ERROR!!:\n", f"{err.__class__}: ", err)
        finally:
            if self.conn:
                self.conn.close()
                self.conn = None

    def url_db_loader(self, category: str, dct: dict):
        '''
        special pymysql function for writing urls in date base after urls loading
        :param category: name of photos category
        :param dct: service dict initializing function
        :return: None
        '''
        self._open_conn_()
        try:
            with self.conn.cursor() as cur:
                for key, value in dct.items():
                    try:
                        cur.execute(
                            f"insert into container values "
                            f"("
                            f"Null, %s, %s, %s, (select category_id from categories where category = %s) "
                            f");",
                            (key, value[0], value[1], category)
                        )
                    except pymysql.IntegrityError:
                        pass
                self.conn.commit()
        except pymysql.Error as err:
            print("!!Data Base ERROR!!:\n", f"{err.__class__}: ", err)
        except AttributeError as err:
            print("!!Data Base Functions ERROR!!:\n", f"{err.__class__}: ", err)
        finally:
            if self.conn:
                self.conn.close()
                self.conn = None

    def select_url(self, category: str):
        """
        :param category: name of category
        :return: dict with 80 urls and their captions or less
        """
        self._open_conn_()
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    f'select url, photographer from container as con '
                    f'inner join categories as cat '
                    f'on con.category_id = cat.category_id '
                    f'where category = %s;',
                    (category,)
                )
                data = cur.fetchall()
                if len(data) > 80:
                    data = r.sample(data, 80)
                dct = {}
                for element in data:
                    dct[element[0]] = element[1]
                return dct
        except pymysql.Error as err:
            print("!!Data Base ERROR!!:\n", f"{err.__class__}: ", err)
        except AttributeError as err:
            print("!!Data Base Functions ERROR!!:\n", f"{err.__class__}: ", err)
        finally:
            if self.conn:
                self.conn.close()
                self.conn = None


config = Config()
db = Database(config)


if __name__ == '__main__':
    print(db.insert_one('users', {'id': 0, 'first_name': 'test'}))
    print(db.select_simple('users', ['*']))
