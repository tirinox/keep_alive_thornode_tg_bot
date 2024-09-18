from datetime import timedelta, datetime
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


def format_timedelta(seconds):
    if not isinstance(seconds, timedelta):
        seconds = timedelta(seconds=seconds)
    return str(seconds).split('.')[0]


MINUTE = 60
HOUR = 60 * MINUTE
DAY = 24 * HOUR
MONTH = 30 * DAY
YEAR = 365 * DAY

NUMBER_CHARS = [chr(i + ord('0')) for i in range(10)] + ['.']
WHITE_SPACE_CHARS = [' ', ',', ';', ':', '\t', '/']


def parse_timespan_to_seconds(span: str, do_float=True):
    try:
        return float(span) if do_float else int(span)
    except ValueError:
        result = 0
        str_for_number = ''
        for symbol in span:
            symbol = symbol.lower()
            if symbol in ['d', 'h', 'm', 's']:
                if str_for_number:
                    try:
                        number = float(str_for_number) if do_float else int(str_for_number)
                    except ValueError:
                        return 'Error! Invalid number: {}'.format(str_for_number)
                    else:
                        multipliers = {
                            's': 1,
                            'm': MINUTE,
                            'h': HOUR,
                            'd': DAY
                        }
                        result += multipliers[symbol] * number
                    finally:
                        str_for_number = ''
                else:
                    return 'Error! Must be some digits before!'
            elif symbol in NUMBER_CHARS:
                str_for_number += symbol
            elif symbol in WHITE_SPACE_CHARS:
                pass
            else:
                return 'Error! Unexpected symbol: {}'.format(symbol)

        if str_for_number:
            return 'Error! Unfinished component in the end: {}'.format(str_for_number)

        return result


def now_ts():
    return datetime.utcnow().timestamp()
