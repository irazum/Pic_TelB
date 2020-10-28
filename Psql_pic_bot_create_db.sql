# "Таблица категорий"
create table categories
(
category_id serial primary key,
category text UNIQUE
);


# "Таблица для хранения всех полученных url-картинок"
create table container
(
id serial primary key,
url text UNIQUE,
url_original text UNIQUE,
photographer text,
category_id integer,
constraint category_id_fk
	foreign key(category_id)
	references categories(category_id)
);


# "Таблица для хранения данных о пользователях бота"
create table users
(
id serial primary key,
is_bot integer check (is_bot in (0,1)),
first_name text,
last_name text,
language_code text
);


# таблица для хранения file_id и автора лайкнутых фото
create table likes_photo
(
file_id text primary key,
author text,
likes_number integer
);


# таблица для сохранения статистики популярности каждой категории за всё время
create table stat_categories
(
category text primary key,
requests_number integer,
constraint stat_categories_fk
    foreign key (category)
    references categories(category)
);

# таблица для сохранения статистики количеста запрошенных картинок каждым юзером
create table stat_users
(
user_id integer primary key,
requests_number integer,
messages_number integer,
constraint stat_users_fk
    foreign key (user_id)
    references users(id)
);

# таблица для сохранения общей статистики активности пользователей за каждый час за всё время
create table stat_time
(
time integer primary key,
requests_number integer,
constraint stat_users_time
    check (time >= 0 and time <= 24 )
);
