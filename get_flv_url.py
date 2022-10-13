from cmath import log
import itertools
import random
import time
import urllib

import fire
import requests

from my_logger import *


logger = get_logger('write_flv_ini')

URL_VSM_VTDU_HTTP_PLAY = 'http://192.168.9.13:8082/vtdu/http/play?gb_code='

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.42'
}

GB_CODE_DAH_2801 = (
    '34020000001921681111',
    '34020000001921681112',
    '34020000001921681113',
    '34020000001921681114',
    '34020000001921681115',
    '34020000001921681116',
)

GB_CODE_DAH_2803 = (
    '34020000003192168112',
    '34020000003192168113',
    '34020000003192168114',
    '34020000003192168115',
    '34020000003192168116',
    '34020000003192168117',
    '34020000003192168118',
    '34020000003192168119',
)


def get_flv_url(path_ini, count=1, index=-1, reversed=False, rand=False, repeat=False):
    if not reversed:
        gb_codes = GB_CODE_DAH_2801 + GB_CODE_DAH_2803
    else:
        gb_codes = GB_CODE_DAH_2803 + GB_CODE_DAH_2801

    max_count = len(gb_codes)

    urls = []
    for i in range(count):
        if 0 <= index < count:
            i = index
        elif not rand:
            i %= max_count
        else:
            i = random.randint(0, max_count - 1)

        while True:
            url_play = URL_VSM_VTDU_HTTP_PLAY + gb_codes[i]
            try:
                data = requests.get(url=url_play, headers=HEADERS, timeout=3).json()
            except requests.exceptions.ReadTimeout:
                logger.warning({'message': 'timeout', 'url': url_play})
                continue
            http_uri = data['http_uri']
            http_port = data['http_port']
            if data['error_code'] == 0 and len(http_uri) > 0:
                break

            data['message'] = url_play
            logger.warning(data)
            time.sleep(1)

        result = urllib.parse.urlparse(http_uri)

        url = f'''http://{result.netloc.partition(':')[0]}:{http_port}/live?{result.query}'''
        if not repeat:
            urls.append(url)
        else:
            urls = list(itertools.repeat(url, count))

        if repeat:
            break
            
    with open(path_ini, 'w') as fp:
        fp.write(f'flv_Cnt={count}\n')
        fp.writelines([f'flv_Str{i+1}={url}\n' for i, url in enumerate(urls)])


if __name__ == '__main__':
    # get_flv_url(path_ini='flv.ini', count=3)
    fire.Fire(get_flv_url)
