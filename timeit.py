import functools
import time

from my_logger import *


def timeit(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        logger = get_logger('ffmpeg')
        start_time = time.time()
        logger.debug({'message': 'started', 'func': func.__name__})
        result = func(*args, **kwargs)
        elasped = time.time() - start_time
        logger.debug({'message': 'finished', 'func': func.__name__, 'elasped': f'{elasped:.3f}s'})
        return elasped, result
    return wrapped
