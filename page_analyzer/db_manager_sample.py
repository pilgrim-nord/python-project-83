import psycopg2
from psycopg2.extras import NamedTupleCursor
from functools import wraps
from psycopg2.extensions import connection


def connect_db(app):
    return psycopg2.connect(app.config['DATABASE_URL'])

def close(conn):
    conn.close()

def execute_in_db(with_commit: bool = False):
    def decorator(func: callable):
        @wraps(func)
        def inner(*args, **kwargs):
            conn = args[0]
            with conn.cursor(cursor_factory=NamedTupleCursor) as cursor:
                result = func(cursor=cursor, *args, **kwargs)
                if with_commit:
                    conn.commit()
                return result

        return inner

    return decorator

@execute_in_db(with_commit=True)
def insert_url(conn, url, cursor=None):  # noqa: pylint=unused-argument
    cursor.execute(
        'INSERT INTO urls (name) VALUES (%s) RETURNING id;',
        (url,)
    )
    return cursor.fetchone().id

@execute_in_db()
def get_url(conn, url_id, cursor):  # noqa: pylint=unused-argument
    cursor.execute(
        'SELECT * FROM urls WHERE id=(%s);', (url_id,)
    )
    return cursor.fetchone()

@execute_in_db()
def check_url_exists(conn, url, cursor):  # noqa: pylint=unused-argument
    cursor.execute(
        'SELECT id, name FROM urls WHERE name=(%s)',
        (url,)
    )
    return cursor.fetchone()


@execute_in_db(with_commit=True)
def insert_check(conn, url_id, url_info, cursor):  # noqa: pylint=unused-argument
    cursor.execute(
        'INSERT INTO url_checks (url_id, status_code, '
        'h1, title, description) '
        'VALUES (%s, %s, %s, %s, %s);',
        (url_id, url_info['status_code'], url_info['h1'],
         url_info['title'], url_info['description'])
    )

@execute_in_db()
def get_url_checks(conn, url_id, cursor):  # noqa: pylint=unused-argument
    cursor.execute(
        'SELECT * FROM url_checks WHERE url_id=(%s) ORDER BY id DESC',
        (url_id,)
    )
    return cursor.fetchall()



@execute_in_db
def check_url_exists(conn, url, cursor):  # noqa: pylint=unused-argument
    cursor.execute(
        'SELECT id, name FROM urls WHERE name=(%s)',
        (url,)
    )
    return cursor.fetchone()

@execute_in_db(with_commit=True)
def insert_check(conn, url_id, url_info, cursor):  # noqa: pylint=unused-argument
    cursor.execute(
        'INSERT INTO url_checks (url_id, status_code, '
        'h1, title, description) '
        'VALUES (%s, %s, %s, %s, %s);',
        (url_id, url_info['status_code'], url_info['h1'],
         url_info['title'], url_info['description'])
    )

@execute_in_db()
def get_urls_with_last_check(conn, cursor):  # noqa: pylint=unused-argument
    cursor.execute('SELECT DISTINCT ON (urls.id) '
                   'urls.id AS id, '
                   'url_checks.id AS check_id, '
                   'url_checks.status_code AS status_code, '
                   'url_checks.created_at AS created_at, '
                   'urls.name AS name '
                   'FROM urls '
                   'LEFT JOIN url_checks ON urls.id=url_checks.url_id '
                   'ORDER BY urls.id DESC, check_id DESC;')
    return cursor.fetchall()

