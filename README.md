## Django ETL Panel

[![python](https://img.shields.io/static/v1?label=python&message=3.8%20|%203.9%20|%203.10&color=informational)](https://github.com/8ubble8uddy/django-etl-panel/actions/workflows/main.yml)
[![dockerfile](https://img.shields.io/static/v1?label=dockerfile&message=published&color=2CB3E8)](https://hub.docker.com/r/8ubble8uddy/django_etl_panel)
[![last updated](https://img.shields.io/static/v1?label=last%20updated&message=may%202023&color=yellow)](https://img.shields.io/static/v1?label=last%20updated&message=may%202022&color=yellow)
[![lint](https://img.shields.io/static/v1?label=lint&message=flake8%20|%20mypy&color=brightgreen)](https://github.com/8ubble8uddy/django-etl-panel/actions/workflows/main.yml)
[![code style](https://img.shields.io/static/v1?label=code%20style&message=WPS&color=orange)](https://wemake-python-styleguide.readthedocs.io/en/latest/)
[![platform](https://img.shields.io/static/v1?label=platform&message=linux%20|%20macos&color=inactive)](https://github.com/8ubble8uddy/django-etl-panel/actions/workflows/main.yml)

### **Описание**

_Целью данной проекта является реализация сервиса для удобного управления процессом ETL, которое включает в себя запуск, остановку и обновление настроек ETL-скрипта. К настройкам относится любая метаинформация: название таблицы, какие поля доставать, какие события обрабатывать и другие настройки. Исходя из задачи была разработана панель управления ETL-процессами на фреймворке [Django](https://www.djangoproject.com) в связке с [Celery](https://docs.celeryq.dev) для распределенного и асинхронного выполнения ETL-задач. Задачи делятся по способу переноса данных: одноразовая выгрузка или постоянная синхронизация. Обработка и анализ данных осуществляется с помощью библиотеки [Pandas](https://pandas.pydata.org). В качестве тестирования и демонстрации результата используются заполненная база данных [SQLite](https://sqlite.org) и два сторонних микросервиса: административная панель c реляционной базой данных [PostgreSQL](https://www.postgresql.org) и API c нереляционным хранилищем документов [ElasticSearch](https://www.elastic.co)._

### **Архитектура**

![Архитектура](https://raw.githubusercontent.com/8ubble8uddy/django-etl-panel/main/architecture/django-etl-panel.png)

* `A` — [Admin Panel](https://github.com/8ubble8uddy/movies-admin-panel) для загрузки и редактирования фильмов.
* `B` — [Async API](https://github.com/8ubble8uddy/movies-async-api) для полнотекстового поиска фильмов.
* `C` — [ETL Panel](https://github.com/8ubble8uddy/django-etl-panel) для управления ETL-процессами.
* `1` — прокси-сервер ***Nginx***, который обрабатывает HTTP-запросы к Django и Celery Flower.
* `2` — фреймворк ***Django*** как основа проекта.
* `3` — база данных ***PostgreSQL*** для хранения метаинформации ETL-процессов.
* `4` — очередь задач ***Celery***, которые выполняют ETL-скрипты в асинхронном фоновом режиме.
* `5` — брокер сообщений ***Redis*** для Celery, чтобы отслеживать наличие новых задач.
* `6` — шедулер ***Celery Beat*** для планирования задач, которые должны выполняться воркером Celery.
* `7` — веб-инструмент ***Celery Flower*** для мониторинга Celery в режиме реального времени.

### **Как запустить проект:**

Клонировать репозиторий и перейти внутри него в директорию ```/infra```:
```
git clone https://github.com/8ubble8uddy/django-etl-panel.git
```
```
cd django-etl-panel/infra/
```

Создать файл .env и добавить настройки для проекта:
```
nano .env
```
```
# PostgreSQL ETL_DATABASE
POSTGRES_ETL_DB=etl_database
POSTGRES_ETL_USER=postgres
POSTGRES_ETL_PASSWORD=postgres
POSTGRES_ETL_HOST=postgres_etl
POSTGRES_ETL_PORT=5432

# PostgreSQL MOVIES_DATABASE
POSTGRES_MOVIES_DB=movies_database
POSTGRES_MOVIES_USER=app
POSTGRES_MOVIES_PASSWORD=123qwe
POSTGRES_MOVIES_HOST=postgres_movies
POSTGRES_MOVIES_PORT=5432

# Elasticsearch
ELASTIC_HOST=elastic
ELASTIC_PORT=9200

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Django ETL Panel
DJANGO_ETL_ALLOWED_HOSTS=localhost,127.0.0.1,[::1],etl_panel
DJANGO_ETL_SECRET_KEY=django-insecure-)%ceik*k#kl+x1tc!_=*n64=88gev=m(j!@c8r-e63q3e^58mo

# Django Admin Panel
DJANGO_ADMIN_SUPERUSER_USERNAME=admin
DJANGO_ADMIN_SUPERUSER_EMAIL=admin@mail.ru
DJANGO_ADMIN_SUPERUSER_PASSWORD=1234
DJANGO_ADMIN_ALLOWED_HOSTS=localhost,127.0.0.1,[::1],admin_panel
DJANGO_ADMIN_SECRET_KEY=django-insecure-_o)z83b+i@jfjzbof_jn9#%dw*5q2yy3r6zzq-3azof#(vkf!#

# FastAPI Async API
FASTAPI_DEBUG=True
```

Развернуть и запустить проект в контейнерах:
```
docker-compose up -d
```

Перейти по ссылке http://127.0.0.1/etl и ввести логин (admin) и пароль(1234):

<kbd><img width="490" alt="джанго админка" src="https://user-images.githubusercontent.com/83628490/234256292-76c0ceef-21d1-490b-a253-460c1238d6d0.png"></kbd>

По секции **Processes** получаем список ETL-процессов:

<kbd><img width="597" alt="процессы2" src="https://user-images.githubusercontent.com/83628490/235306530-0e5a076a-600d-4513-8bb8-874658a0a7fe.png"></kbd>

Выбираем процесс начиная снизу, меняем поле **Status** на ```Active``` и сохраняем:

<kbd><img width="540" alt="активация2" src="https://user-images.githubusercontent.com/83628490/235306551-44d89581-d99c-47ec-8b35-8c6fec1568c1.png"></kbd>

Процессы с PostgreSQL в Elasticsearch выполняют синхронизацию данных:

<kbd><img width="511" alt="синк2" src="https://user-images.githubusercontent.com/83628490/235306567-97fc0ac4-6902-44ee-84dd-8632d73f03a6.png"></kbd>

Проверить результат загрузки данных из SQLite в PostgreSQL можно по ссылке http://127.0.0.1/admin (логин: admin, пароль: 1234):

<kbd><img width="706" alt="результат1" src="https://user-images.githubusercontent.com/83628490/234261984-d8be073f-0669-4a1c-b418-135b494465f4.png"></kbd>

И результат синхронизации из PostgreSQL в Elasticsearch по ссылке http://127.0.0.1/api/v1/films:

<kbd><img width="606" alt="результат2" src="https://user-images.githubusercontent.com/83628490/234263559-5781c827-f71b-4382-afd3-f3ecf28da0ff.png"></kbd>

### Автор: Герман Сизов