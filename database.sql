CREATE TABLE IF NOT EXISTS urls (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS url_checks (
    id SERIAL PRIMARY KEY,
    url_id BIGINT REFERENCES urls (id) ON DELETE CASCADE NOT NULL,
    status_code TEXT,
    h1 TEXT,
    title TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    postgresql://dmelekhov:LrIxmAABzRK9RUfO2zf5ypXTXyFmPGRX@dpg-d3qe7ggdl3ps73bsk6p0-a.oregon-postgres.render.com/project83_qike
    Добрый день! У меня написано, что осталось 268 дней Premium. при попытке создать новый портфель


127.0.0.1 - - [06/Nov/2025 11:55:40] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [06/Nov/2025 11:55:48] "POST /urls/ HTTP/1.1" 422 -

127.0.0.1 - - [06/Nov/2025 11:56:18] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [06/Nov/2025 11:56:28] "POST /urls HTTP/1.1" 422 -
