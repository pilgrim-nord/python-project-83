cat > setup.sh << 'EOF'
#!/bin/bash
set -e

# Создаём структуру
mkdir -p page_analyzer templates/{includes,urls,errors} tests .github/workflows static

# pyproject.toml
cat > pyproject.toml << 'PYPROJECT'
[project]
name = "page-analyzer"
version = "0.1.0"
description = "Page Analyzer — SEO checker (Hexlet)"
authors = [{name = "pilgrim-nord", email = "your@email.com"}]
dependencies = [
    "flask>=3.0.0",
    "psycopg2-binary>=2.9.9",
    "requests>=2.31.0",
    "beautifulsoup4>=4.12.2",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.3",
    "flake8>=7.0.0",
]

[tool.uv]
python = "3.11"
PYPROJECT

# Makefile
cat > Makefile << 'MAKEFILE'
install:
	uv sync --dev

start:
	uv run python -m page_analyzer.app

lint:
	uv run flake8 page_analyzer tests

test:
	uv run pytest tests

reqs:
	uv export --format=requirements-txt > requirements.txt
MAKEFILE

# .env.example
cat > .env.example << 'ENV'
SECRET_KEY=super-secret-key-change-in-prod!!
DATABASE_URL=postgresql://user:pass@localhost:5432/page_analyzer
ENV

# README.md
cat > README.md << 'README'
# Page Analyzer (Hexlet)

Веб-приложение для анализа страниц на SEO-подходность.

## Запуск

1. \`make install\`
2. Скопируй \`.env.example\` → \`.env\` и настрой
3. Создай БД (см. ниже)
4. \`make start\`

## БД (PostgreSQL)
\`\`\`sql
CREATE DATABASE page_analyzer;
\\c page_analyzer
CREATE TABLE urls (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE url_checks (
    id SERIAL PRIMARY KEY,
    url_id INTEGER REFERENCES urls(id),
    status_code INTEGER,
    h1 TEXT,
    title VARCHAR,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
\`\`\`

## Команды
- \`make lint\` — линтинг
- \`make test\` — тесты
- \`make start\` — запуск (localhost:5000)
README

# .gitignore
cat > .gitignore << 'GITIGNORE'
__pycache__/
*.pyc
.venv/
.env
.pytest_cache/
HTMLcov/
GITIGNORE

# page_analyzer/__init__.py
cat > page_analyzer/__init__.py << 'INIT'
from .app import app

__all__ = ["app"]
INIT

# page_analyzer/db_manager.py (с декораторами, простой и надёжный)
cat > page_analyzer/db_manager.py << 'DB'
import psycopg2
from psycopg2.extras import NamedTupleCursor
from functools import wraps
from flask import current_app

def execute_in_db(with_commit=False):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            conn = args[0]
            with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
                result = func(cur=cur, *args, **kwargs)
                if with_commit:
                    conn.commit()
                return result
        return wrapper
    return decorator

def connect_db():
    return psycopg2.connect(current_app.config['DATABASE_URL'])

def close(conn):
    if conn:
        conn.close()

@execute_in_db(with_commit=True)
def insert_url(cur, conn, url):
    cur.execute("INSERT INTO urls (name) VALUES (%s) RETURNING id;", (url,))
    return cur.fetchone().id

@execute_in_db()
def get_url(cur, conn, url_id):
    cur.execute("SELECT * FROM urls WHERE id = %s;", (url_id,))
    return cur.fetchone()

@execute_in_db()
def check_url_exists(cur, conn, url):
    cur.execute("SELECT id, name FROM urls WHERE name = %s;", (url,))
    return cur.fetchone()

@execute_in_db(with_commit=True)
def insert_check(cur, conn, url_id, url_info):
    cur.execute(
        "INSERT INTO url_checks (url_id, status_code, h1, title, description) VALUES (%s, %s, %s, %s, %s);",
        (url_id, url_info.get('status_code'), url_info.get('h1'), url_info.get('title'), url_info.get('description'))
    )

@execute_in_db()
def get_url_checks(cur, conn, url_id):
    cur.execute("SELECT * FROM url_checks WHERE url_id = %s ORDER BY id DESC;", (url_id,))
    return cur.fetchall()

@execute_in_db()
def get_urls_with_last_check(cur, conn):
    cur.execute(
        "SELECT DISTINCT ON (urls.id) urls.id, urls.name, url_checks.id as check_id, "
        "url_checks.status_code, url_checks.created_at FROM urls "
        "LEFT JOIN url_checks ON urls.id = url_checks.url_id "
        "ORDER BY urls.id DESC, url_checks.id DESC;"
    )
    return cur.fetchall()
DB

# page_analyzer/utils.py
cat > page_analyzer/utils.py << 'UTILS'
import re
from urllib.parse import urlparse, urljoin

def normalize_url(url):
    parsed = urlparse(url)
    if not parsed.scheme:
        url = 'https://' + url
    return urljoin(url, '/')

def validate_url(url):
    pattern = re.compile(
        r'^https?://'  # scheme
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # port
        r'(?:/?|[/?]\S*)$', re.IGNORECASE)
    if pattern.match(url):
        return ''
    return 'Некорректный URL'
UTILS

# page_analyzer/page_checker.py
cat > page_analyzer/page_checker.py << 'CHECKER'
from bs4 import BeautifulSoup

def extract_page_data(response):
    soup = BeautifulSoup(response.text, 'html.parser')
    title = (soup.title.string or '')[:60]
    h1 = (soup.h1.string or '')[:60] if soup.h1 else ''
    desc_tag = soup.find('meta', attrs={'name': 'description'})
    description = (desc_tag['content'] or '')[:160] if desc_tag else ''
    return {
        'status_code': response.status_code,
        'h1': h1,
        'title': title,
        'description': description
    }
CHECKER

# page_analyzer/app.py
cat > page_analyzer/app.py << 'APP'
import os
from flask import Flask, render_template, redirect, flash, url_for, request, abort
from dotenv import load_dotenv
import requests
from page_analyzer.db_manager import (
    connect_db, close, insert_url, get_url, check_url_exists,
    insert_check, get_url_checks, get_urls_with_last_check
)
from page_analyzer.utils import validate_url, normalize_url
from page_analyzer.page_checker import extract_page_data

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-me')
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')

if not app.config['DATABASE_URL']:
    raise RuntimeError('DATABASE_URL required in .env')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/urls/')
def urls():
    conn = connect_db()
    try:
        urls_list = get_urls_with_last_check(conn, None)
        return render_template('urls/list.html', urls=urls_list)
    finally:
        close(conn)

@app.route('/urls/<int:url_id>/')
def url(url_id):
    conn = connect_db()
    try:
        url_obj = get_url(conn, None, url_id)
        if not url_obj:
            abort(404)
        checks = get_url_checks(conn, None, url_id)
        return render_template('urls/detail.html', url=url_obj, checks=checks)
    finally:
        close(conn)

@app.post('/urls/')
def add_url():
    url = request.form.get('url', '').strip()
    if not url:
        flash('URL обязателен', 'danger')
        return render_template('index.html'), 422

    normalized = normalize_url(url)
    error = validate_url(normalized)
    if error:
        flash(error, 'danger')
        return render_template('index.html', url=url), 422

    conn = connect_db()
    try:
        exists = check_url_exists(conn, None, normalized)
        if exists:
            flash('Страница уже существует', 'info')
            url_id = exists.id
        else:
            url_id = insert_url(conn, None, normalized)
            flash('Страница успешно добавлена', 'success')
        return redirect(url_for('url', url_id=url_id))
    finally:
        close(conn)

@app.post('/urls/<int:url_id>/checks/')
def check(url_id):
    conn = connect_db()
    try:
        url_obj = get_url(conn, None, url_id)
        if not url_obj:
            abort(404)

        try:
            resp = requests.get(url_obj.name, timeout=10, allow_redirects=True)
            resp.raise_for_status()
        except requests.RequestException:
            flash('Произошла ошибка при проверке', 'danger')
            return redirect(url_for('url', url_id=url_id))

        info = extract_page_data(resp)
        insert_check(conn, None, url_id, info)
        flash('Страница успешно проверена', 'success')
        return redirect(url_for('url', url_id=url_id))
    finally:
        close(conn)

@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
APP

# templates/base.html
cat > templates/base.html << 'BASE'
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
    <title>Анализатор страниц</title>
</head>
<body class="d-flex flex-column min-vh-100">
    <header class="flex-shrink-0 bg-light">
        {% include 'includes/nav.html' %}
    </header>
    <main class="flex-grow-1">
        <div class="container-lg py-4">
            {% include 'includes/messages.html' %}
            {% block content %}{% endblock %}
        </div>
    </main>
    {% include 'includes/footer.html' %}
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz" crossorigin="anonymous"></script>
</body>
</html>
BASE

# templates/includes/nav.html
cat > templates/includes/nav.html << 'NAV'
<nav class="navbar navbar-expand-lg navbar-light">
    <div class="container">
        <a class="navbar-brand" href="{{ url_for('index') }}">Анализатор страниц</a>
        <ul class="navbar-nav ms-auto">
            <li class="nav-item"><a class="nav-link" href="{{ url_for('index') }}">Главная</a></li>
            <li class="nav-item"><a class="nav-link" href="{{ url_for('urls') }}">Сайты</a></li>
        </ul>
    </div>
</nav>
NAV

# templates/includes/messages.html
cat > templates/includes/messages.html << 'MSG'
{% with messages = get_flashed_messages(with_categories=true) %}
{% if messages %}
    {% for category, message in messages %}
    <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show" role="alert">
        {{ message }}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>
    {% endfor %}
{% endif %}
{% endwith %}
MSG

# templates/includes/footer.html
cat > templates/includes/footer.html << 'FOOT'
<footer class="mt-auto bg-light py-3 border-top">
    <div class="container text-center">
        <small class="text-muted">&copy; 2025 pilgrim-nord. Hexlet project.</small>
    </div>
</footer>
FOOT

# templates/index.html
cat > templates/index.html << 'INDEX'
{% extends "base.html" %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-lg-8">
        <div class="card">
            <div class="card-body">
                <h1 class="card-title">Добавьте URL для проверки</h1>
                <form method="post" action="{{ url_for('add_url') }}">
                    <div class="mb-3">
                        <label class="form-label">URL</label>
                        <input type="url" class="form-control" name="url" required>
                    </div>
                    <button type="submit" class="btn btn-primary">Добавить</button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
INDEX

# templates/urls/list.html
cat > templates/urls/list.html << 'LIST'
{% extends "base.html" %}
{% block content %}
<h1>Сайты</h1>
<table class="table table-striped">
    <thead>
        <tr>
            <th>ID</th>
            <th>URL</th>
            <th>Последняя проверка</th>
            <th>Код ответа</th>
        </tr>
    </thead>
    <tbody>
        {% for u in urls %}
        <tr>
            <td>{{ u.id }}</td>
            <td><a href="{{ url_for('url', url_id=u.id) }}">{{ u.name }}</a></td>
            <td>{{ u.created_at or '' }}</td>
            <td class="{% if u.status_code == 200 %}table-success{% elif u.status_code >= 400 %}table-danger{% else %}table-warning{% endif %}">
                {{ u.status_code or '—' }}
            </td>
        </tr>
        {% else %}
        <tr><td colspan="4" class="text-center">Сайты не добавлены</td></tr>
        {% endfor %}
    </tbody>
</table>
{% endblock %}
LIST

# templates/urls/detail.html
cat > templates/urls/detail.html << 'DETAIL'
{% extends "base.html" %}
{% block content %}
<h1>{{ url.name }}</h1>
<div class="row mb-4">
    <div class="col-md-6">
        <table class="table table-bordered">
            <tr><th>ID</th><td>{{ url.id }}</td></tr>
            <tr><th>Имя</th><td>{{ url.name }}</td></tr>
            <tr><th>Создан</th><td>{{ url.created_at }}</td></tr>
        </table>
    </div>
</div>
<h2>Проверки</h2>
<form method="post" action="{{ url_for('check', url_id=url.id) }}" class="mb-4">
    <button type="submit" class="btn btn-primary">Запустить проверку</button>
</form>
{% if checks %}
<table class="table table-striped">
    <thead>
        <tr>
            <th>ID</th>
            <th>Код</th>
            <th>h1</th>
            <th>title</th>
            <th>description</th>
            <th>Создан</th>
        </tr>
    </thead>
    <tbody>
        {% for c in checks %}
        <tr>
            <td>{{ c.id }}</td>
            <td class="{% if c.status_code == 200 %}table-success{% elif c.status_code >= 400 %}table-danger{% else %}table-warning{% endif %}">
                {{ c.status_code or '—' }}
            </td>
            <td>{{ c.h1 or '—' }}</td>
            <td>{{ c.title or '—' }}</td>
            <td>{{ c.description or '—' }}</td>
            <td>{{ c.created_at }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% else %}
<p class="text-muted">Проверок не проводилось</p>
{% endif %}
{% endblock %}
DETAIL

# templates/errors/404.html
cat > templates/errors/404.html << '404'
{% extends "base.html" %}
{% block content %}
<div class="text-center">
    <h1>404 — Страница не найдена</h1>
    <a href="{{ url_for('index') }}" class="btn btn-primary">На главную</a>
</div>
{% endblock %}
404

# templates/errors/500.html
cat > templates/errors/500.html << '500'
{% extends "base.html" %}
{% block content %}
<div class="text-center">
    <h1>500 — Ошибка сервера</h1>
    <a href="{{ url_for('index') }}" class="btn btn-primary">На главную</a>
</div>
{% endblock %}
500

# tests/test_app.py (простой тест)
cat > tests/test_app.py << 'TEST'
import pytest
from page_analyzer.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index(client):
    rv = client.get('/')
    assert rv.status_code == 200
TEST

# .github/workflows/tests.yml
cat > .github/workflows/tests.yml << 'CI'
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Install uv
      run: curl -LsSf https://astral.sh/uv/install.sh | sh
    - name: Install deps
      run: uv sync --dev
    - name: Lint
      run: uv run flake8 page_analyzer tests
    - name: Test
      run: uv run pytest tests
CI

echo "✅ Все файлы созданы!"
echo "Теперь:"
echo "1. git add ."
echo "2. git commit -m 'Initial commit: Page Analyzer'"
echo "3. git push"
EOF

chmod +x setup.sh
./setup.sh