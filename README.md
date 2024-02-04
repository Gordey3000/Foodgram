# Foodgram - продуктовый помощник 

Foodgram - это онлайн-сервис для любителей готовить. Пользователи данного сервиса могут публиковать рецепты, делиться рецептами друг с другом, добавлять понравившиеся рецепты в избранное и следить за обновлениями других пользователей. Также Foodgram сможет подсчитать для Вас необходимое количество ингредиентов всех выбранных блюд и составить из них список покупок, который можно скачать и взять с собой в магазин.

### Как запустить проект в контейнерах локально:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/gordey3000/foodgram-project-react.git
```

```
cd foodgram-project-react/infra
```

Установить Docker Desktop на Ваш компьютер и запустить его.

Создать директории infra файл .env и заполнить его своими данными:

```
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<your_password>
DB_HOST=foodgram_db
DB_PORT=5432
SECRET_KEY=<your_secret_key>
ALLOWED_HOSTS=localhost you_can_add_your_host_here
```

Запустить оркестр контейнеров:

```
docker compose up
```

Дождаться сборки и запуска всех контейнеров и в другом окне терминала выполнить миграции:
```
docker compose exec backend python manage.py makemigrations
```

```
docker compose exec backend python manage.py migrate 
```

Собрать и скопировать статику Django:

```
docker compose exec backend python manage.py collectstatic
```
```
docker compose exec backend cp -r /app/collected_static/. /backend_static/static/ 
```
```
docker compose exec backend python manage.py load_ingr - загрузить ингредиенты из списка. 
```
```
docker compose exec backend python manage.py load_tags - загрузить тэги из списка. 
```
Проект будет доступен по адресу: http://localhost/