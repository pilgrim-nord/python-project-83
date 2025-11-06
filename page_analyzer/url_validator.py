import validators
from urllib.parse import urlparse


def normalize_url(url):
    parsed = urlparse(url)
    scheme = parsed.scheme or 'https'
    return f'{scheme}://{parsed.netloc}'


def validate_url(url):
    if not url:
        return 'URL обязателен для заполнения'

    if len(url) > 255:
        return 'URL превышает 255 символов'

    if not validators.url(url):
        return 'Некорректный URL'

    return None

