# Foodgram

## Быстрый старт

### 1. Клонируйте репозиторий

```bash
git clone <https://github.com/mistik2000/foodgram-st.git>
cd foodgram-st
```

### 2. Создайте файл окружения

В папке `backend` создайте файл `.env` со следующим содержимым (пример):

```
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
DB_HOST=db
DB_PORT=5432
```

### 3. Запустите проект

Перейдите в папку `infra` и выполните:

```bash
cd infra
docker compose up -d
```

- После сборки и запуска контейнеров:
  - Фронтенд будет доступен по адресу: [http://localhost/](http://localhost/)
  - Документация API: [http://localhost/api/docs/](http://localhost/api/docs/)

### 4. Примените миграции

После первого запуска контейнеров выполните:

```bash
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate

```

### 5. Импортируйте ингредиенты (обязательно для прохождения тестов)

```bash
docker compose exec backend python manage.py load_ingredients
```

**Важно:**
- Без этого шага тесты, связанные с ингредиентами, не пройдут!
- Если вы сбрасываете базу данных, повторите импорт ингредиентов.

### 6. Создайте суперпользователя (админ-панель)

```bash
docker compose exec backend python manage.py createsuperuser
```
- Админка будет доступна по адресу: [http://localhost/admin/](http://localhost/admin/)

---

## Зависимости

- Python 3.10+
- Docker, Docker Compose
- Node.js (для разработки фронтенда)

---

## Примечания

- Все данные хранятся в volume postgres_data и media_value.
- Для повторного сброса базы данных удалите volume postgres_data и повторите миграции/импорт ингредиентов.
- Для прохождения тестов обязательно загрузите ингредиенты из data/ingredients.json.

---

Автор: Ревенко Софья Сергеевна 

