from psycopg2.extras import NamedTupleCursor
from contextlib import contextmanager
from typing import Optional, List, Dict, Any


class UrlRepository:
    def __init__(self, conn):
        self.conn = conn

    @contextmanager
    def _cursor(self, named_tuple=True):
        cursor_factory = NamedTupleCursor if named_tuple else None
        with self.conn.cursor(cursor_factory=cursor_factory) as cur:
            try:
                yield cur
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise
            finally:
                pass

    # === URL ===

    def insert_url(self, url: str) -> int:
        with self._cursor(named_tuple=True) as cur:
            cur.execute(
                "INSERT INTO urls (name) VALUES (%s) RETURNING id;",
                (url,)
            )
            return cur.fetchone().id

    def get_url(self, url_id: int) -> Optional[NamedTupleCursor]:
        with self._cursor(named_tuple=True) as cur:
            cur.execute("SELECT * FROM urls WHERE id = %s;", (url_id,))
            return cur.fetchone()

    def check_url_exists(self, url: str) -> Optional[NamedTupleCursor]:
        with self._cursor(named_tuple=True) as cur:
            cur.execute("SELECT id, name FROM urls WHERE name = %s;", (url,))
            return cur.fetchone()

    # === CHECKS ===

    def insert_check(self, url_id: int, url_info: Dict[str, Any]) -> None:
        with self._cursor(named_tuple=False) as cur:
            cur.execute(
                """
                INSERT INTO url_checks 
                (url_id, status_code, h1, title, description) 
                VALUES (%s, %s, %s, %s, %s);
                """,
                (
                    url_id,
                    url_info.get('status_code'),
                    url_info.get('h1'),
                    url_info.get('title'),
                    url_info.get('description'),
                )
            )

    def get_url_checks(self, url_id: int) -> List[NamedTupleCursor]:
        with self._cursor(named_tuple=True) as cur:
            cur.execute(
                "SELECT * FROM url_checks WHERE url_id = %s ORDER BY id DESC;",
                (url_id,)
            )
            return cur.fetchall()

    def get_urls_with_last_check(self) -> List[NamedTupleCursor]:
        with self._cursor(named_tuple=True) as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (urls.id)
                    urls.id AS id,
                    urls.name AS name,
                    url_checks.id AS check_id,
                    url_checks.status_code AS status_code,
                    url_checks.created_at AS created_at
                FROM urls
                LEFT JOIN url_checks ON urls.id = url_checks.url_id
                ORDER BY urls.id DESC, url_checks.id DESC;
                """
            )
            return cur.fetchall()