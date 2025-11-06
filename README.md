# Page Analyzer

Веб-приложение для анализа веб-страниц. Позволяет добавлять URL-адреса и проверять их, извлекая ключевую информацию со страниц.

### Hexlet tests and linter status:
[![Actions Status](https://github.com/pilgrim-nord/python-project-83/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/pilgrim-nord/python-project-83/actions/workflows/hexlet-check.yml)

[![Python application](https://github.com/pilgrim-nord/python-project-83/actions/workflows/linter.yml/badge.svg)](https://github.com/pilgrim-nord/python-project-83/actions/workflows/linter.yml)

**Демо:** https://python-project-83-tp4w.onrender.com/

## Возможности

- ✅ Добавление URL-адресов с валидацией
- ✅ Проверка доступности страниц
- ✅ Извлечение метаданных:
  - HTTP статус-код
  - Заголовок H1
  - Title страницы
  - Meta description
- ✅ История проверок для каждого URL
- ✅ Список всех добавленных URL с последней проверкой

## Технологии

- **Python 3.13+**
- **Flask** — веб-фреймворк
- **PostgreSQL** — база данных
- **BeautifulSoup4** — парсинг HTML
- **Requests** — HTTP-запросы
- **Validators** — валидация URL
- **Gunicorn** — WSGI-сервер для production

## Установка

### Требования

- Python 3.13 или выше
- PostgreSQL
- [uv](https://github.com/astral-sh/uv) — менеджер пакетов

### Шаги установки

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd python-project-83
```

2. Установите зависимости:
```bash
make install
# или
uv sync
```

3. Создайте базу данных и выполните миграции:
```bash
psql -U postgres -f database.sql
```

4. Создайте файл `.env` в корне проекта:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
SECRET_KEY=your-secret-key-here
```

## Запуск

### Режим разработки

```bash
make dev
# или
uv run flask --debug --app page_analyzer:app run
```

Приложение будет доступно по адресу: http://localhost:5000

### Production режим

```bash
make start PORT=8000
# или
uv run gunicorn -w 5 -b 0.0.0.0:8000 page_analyzer:app
```

## Использование

1. **Добавление URL**: Введите URL-адрес на главной странице и нажмите "Проверить"
2. **Просмотр списка**: Перейдите в раздел "Сайты" для просмотра всех добавленных URL
3. **Проверка страницы**: На странице деталей URL нажмите "Проверить" для выполнения новой проверки
4. **История проверок**: На странице деталей отображается история всех проверок с извлеченными данными

## Структура проекта

```
python-project-83/
├── page_analyzer/          # Основной пакет приложения
│   ├── app.py              # Flask приложение и маршруты
│   ├── db_manager.py       # Работа с базой данных
│   ├── parser.py           # Парсинг HTML страниц
│   ├── url_validator.py    # Валидация и нормализация URL
│   └── templates/          # HTML шаблоны
├── tests/                  # Тесты
├── database.sql            # SQL схема базы данных
├── pyproject.toml          # Конфигурация проекта
├── Makefile               # Команды для разработки
└── README.md              # Документация
```

## Разработка

### Линтинг

```bash
make lint
# или
uv run ruff check page_analyzer
```

### Тестирование

```bash
make test
```

## Лицензия

Этот проект создан в рамках обучения на [Hexlet](https://hexlet.io).
