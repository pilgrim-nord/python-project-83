import os
import requests
import psycopg2
from flask import (
    Flask, render_template, redirect, flash,
    url_for, request, abort
)
from .db_manager import UrlRepository
from dotenv import load_dotenv
# from page_analyzer import db_manager as db
from .utils import validate_url, normalize_url
from .page_checker import extract_page_data

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')

def get_connection():
    return psycopg2.connect(DATABASE_URL)

# Константа для таймаута
REQUESTS_TIMEOUT = 10

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/urls/')
def show_urls_page():
    conn = get_connection()
    try:
        repo = UrlRepository(conn)
        urls_check = repo.get_urls_with_last_check()
        return render_template('urls/list.html', urls_check=urls_check)
    finally:
        conn.close()


@app.route('/urls/<int:url_id>/')
def show_url_page(url_id):
    conn = get_connection()
    try:
        repo = UrlRepository(conn)
        url = repo.get_url(url_id)
        if not url:
            return abort(404)
        checks = repo.get_url_checks(url_id)
        return render_template('urls/detail.html', url=url, checks=checks)
    finally:
        conn.close()


@app.post('/urls/')
def add_url():
    raw_url = request.form.get('url', '').strip()
    error = None

    if not raw_url:
        error = 'URL обязателен'
    else:
        normal_url = normalize_url(raw_url)
        validation_error = validate_url(normal_url)
        if validation_error:
            error = validation_error
        else:
            conn = get_connection()
            try:
                repo = UrlRepository(conn)
                existed_url = repo.check_url_exists(normal_url)
                if existed_url:
                    flash('Страница уже существует', 'info')
                    return redirect(url_for('show_url_page', url_id=existed_url.id))
                else:
                    url_id = repo.insert_url(normal_url)
                    flash('Страница успешно добавлена', 'success')
                    return redirect(url_for('show_url_page', url_id=url_id))
            finally:
                conn.close()

    # ← Только сюда попадаем при ошибках валидации
    flash(error, 'danger')
    # Важно: передаём все переменные, которые ожидает index.html
    conn = get_connection()
    try:
        repo = UrlRepository(conn)
        urls = repo.get_urls_with_last_check()
    finally:
        conn.close()

    return render_template('index.html', url=raw_url, urls=urls), 422

@app.post('/urls/<int:url_id>/checks/')
def check_url_page(url_id):
    conn = get_connection()
    try:
        repo = UrlRepository(conn)
        url = repo.get_url(url_id)
        if not url:
            return abort(404)

        try:
            response = requests.get(
                url.name,
                timeout=REQUESTS_TIMEOUT,
                allow_redirects=True
            )
            response.raise_for_status()
        except requests.RequestException:
            flash('Произошла ошибка при проверке', 'danger')
            return redirect(url_for('show_url_page', url_id=url_id))

        url_info = extract_page_data(response)
        repo.insert_check(url_id, url_info)
        flash('Страница успешно проверена', 'success')
        return redirect(url_for('show_url_page', url_id=url_id))
    finally:
        conn.close()


# === Обработка ошибок ===

@app.errorhandler(404)
def page_not_found(_):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_server_error(_):
    return render_template('errors/500.html'), 500