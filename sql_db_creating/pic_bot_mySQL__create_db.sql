# "Таблица категорий"
create table categories
(
category_id integer primary key Auto_Increment,
category varchar(50) UNIQUE
);


# "Таблица для хранения всех полученных url-картинок"
create table container
(
id int primary key auto_increment,
url varchar(200) unique,
url_original varchar(200) unique,
photographer varchar(50),
category_id int,
constraint category_id_fk
	foreign key(category_id)
	references categories(category_id)
);


# "Таблица для хранения данных о пользователях бота"
create table users
(
id integer primary key,
is_bot integer check (is_bot in (0,1)),
first_name varchar(50),
last_name varchar(50),
language_code varchar(10)
);


# таблица для хранения file_id и автора лайкнутых фото
create table likes_photo
(
photo_id varchar(150) primary key,
author varchar(50),
likes_number integer
);


# таблица для сохранения статистики популярности каждой категории за всё время
create table stat_categories
(
category varchar(50) primary key,
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
