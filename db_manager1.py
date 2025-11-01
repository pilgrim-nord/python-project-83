import psycopg2
from psycopg2.extras import NamedTupleCursor


class UrlRepository:
    def __init__(self, conn):
        self.conn = conn

    def insert_url(self, url):
        with self.conn.cursor(cursor_factory=NamedTupleCursor) as cur:
            cur.execute(
                'INSERT INTO urls (name) VALUES (%s) RETURNING id;',
                (url,)
            )
            url_id = cur.fetchone().id
        self.conn.commit()
        return url_id

    def get_url(self, url_id):
        with self.conn.cursor(cursor_factory=NamedTupleCursor) as cur:
            cur.execute(
                'SELECT * FROM urls WHERE id = %s;',
                (url_id,)
            )
            return cur.fetchone()

    def check_url_exists(self, url):
        with self.conn.cursor(cursor_factory=NamedTupleCursor) as cur:
            cur.execute(
                'SELECT id, name FROM urls WHERE name = %s;',
                (url,)
            )
            return cur.fetchone()

    def insert_check(self, url_id, url_info):
        with self.conn.cursor() as cur:
            cur.execute(
                'INSERT INTO url_checks (url_id, status_code, h1, title, description) '
                'VALUES (%s, %s, %s, %s, %s);',
                (url_id, url_info['status_code'], url_info['h1'], url_info['title'], url_info['description'])
            )
        self.conn.commit()

    def get_url_checks(self, url_id):
        with self.conn.cursor(cursor_factory=NamedTupleCursor) as cur:
            cur.execute(
                'SELECT * FROM url_checks WHERE url_id = %s ORDER BY id DESC;',
                (url_id,)
            )
            return cur.fetchall()

    def get_urls_with_last_check(self):
        with self.conn.cursor(cursor_factory=NamedTupleCursor) as cur:
            cur.execute(
                'SELECT DISTINCT ON (urls.id) '
                'urls.id AS id, '
                'url_checks.id AS check_id, '
                'url_checks.status_code AS status_code, '
                'url_checks.created_at AS created_at, '
                'urls.name AS name '
                'FROM urls '
                'LEFT JOIN url_checks ON urls.id = url_checks.url_id '
                'ORDER BY urls.id DESC, check_id DESC;'
            )
            return cur.fetchall()
