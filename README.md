# Планировщик поездок — вариант №9

**Автор:** Усмонова Марямхон Бахтиёрджоновна  
**Группа:** ИСиП1-9-24  
**Технологии:** Python, FastAPI, SQLAlchemy 2.0, SQLite, Alembic, HTML, CSS, JavaScript.

## Возможности

- Регистрация, вход и выход через cookie-сессии.
- Пароли хранятся только в виде PBKDF2-SHA256-хешей.
- Создание, просмотр, редактирование и удаление собственных поездок.
- План по дням: дата, время, место, стоимость, отметка выполнения.
- Поиск, фильтрация по статусу, сортировка, постраничный вывод.
- Сводная статистика и группировка поездок по месяцам.
- Выгрузка собственных поездок в CSV.
- Администратор может просматривать всех пользователей и поездки.
- Изоляция данных пользователей: чужие поездки и пункты плана недоступны.

## Быстрый запуск

Требуется Python 3.10+ (рекомендуется Python 3.12).

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:SECRET_KEY = "change-this-to-a-long-random-secret-key-12345"
alembic upgrade head
uvicorn app.main:app --reload
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
alembic upgrade head
uvicorn app.main:app --reload
```

Откройте http://127.0.0.1:8000. Swagger-документация API: http://127.0.0.1:8000/docs.

**Важно:** секретный ключ задаётся переменной окружения. Для публикации в интернете необходимо настроить HTTPS и в `app/main.py` переключить `https_only=True`. SQLite-файл `app.db` не добавляется в Git.

## Структура

```text
app/
  main.py               # FastAPI и маршрутизация
  database.py           # подключение SQLite и сессии
  models.py             # SQLAlchemy ORM
  schemas.py            # Pydantic-схемы
  security.py           # хеширование паролей
  deps.py               # зависимости доступа
  routers/
    auth.py             # регистрация и вход
    trips.py            # поездки, статистика, CSV
    plan_items.py       # план по дням
    admin.py            # просмотр для администратора
  static/
    index.html
    style.css
    app.js
migrations/
  env.py
  versions/0001_initial.py
alembic.ini
requirements.txt
REPORT.md
DEFENSE.md
```

## API

| Метод | Адрес | Назначение |
|---|---|---|
| POST | /api/auth/register | регистрация |
| POST | /api/auth/login | вход |
| POST | /api/auth/logout | выход |
| GET | /api/auth/me | текущий пользователь |
| POST | /api/auth/change-password | смена пароля |
| GET | /api/trips | список, поиск, фильтры и пагинация |
| POST | /api/trips | создание поездки |
| GET | /api/trips/{trip_id} | одна поездка |
| PATCH | /api/trips/{trip_id} | изменение |
| DELETE | /api/trips/{trip_id} | удаление |
| GET | /api/trips/stats | общая и помесячная статистика |
| GET | /api/trips/export.csv | выгрузка CSV |
| GET | /api/trips/{trip_id}/plan-items | пункты плана |
| POST | /api/trips/{trip_id}/plan-items | добавить пункт |
| PATCH | /api/plan-items/{item_id} | изменить пункт |
| DELETE | /api/plan-items/{item_id} | удалить пункт |
| GET | /api/admin/users | все пользователи (админ) |
| GET | /api/admin/trips | все поездки (админ) |

Для назначения администратора **в локальной учебной базе** после регистрации используйте SQLite:

```sql
UPDATE users SET is_admin = 1 WHERE username = 'ваш_логин';
```

После этого выйдите и войдите снова. В публичном приложении назначать администраторов следует только через защищённую административную процедуру.

## Проверка

1. Зарегистрируйте два аккаунта.
2. Создайте поездку первым пользователем, добавьте пункт плана.
3. Войдите вторым пользователем и попробуйте открыть ID поездки первого через API: ожидается HTTP 404.
4. Проверьте создание поездки с датой окончания раньше даты начала: HTTP 422.
5. Проверьте фильтры, CSV, статистику и удаление поездки с пунктами плана.

## Примечание

Это учебный проект, не коммерческая система бронирования. Бюджет задаётся в рублях для примера; приложение не проводит платежи и не резервирует билеты.
