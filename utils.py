from urllib import parse


def to_json_bool(b):
    return 'true' if b else 'false'


BLOCK_TIME = 6


def normalize_url(url: str, path_do_add=''):
    if not url.startswith('http'):
        url = 'https://' + url

    # parse url
    parsed = parse.urlparse(url)

    # remove path and query
    url = f"{parsed.scheme}://{parsed.netloc}"

    if path_do_add:
        path_do_add = path_do_add.lstrip('/')
        url = f"{url}/{path_do_add}"

    return url
