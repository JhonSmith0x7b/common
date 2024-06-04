import sys
import logging
import datetime
from collections.abc import Callable, Iterator
from functools import wraps
import traceback
import time
import asyncio
import string


def init_log(log_path="", level=logging.INFO) -> None:
    log_formatter = logging.Formatter("%(asctime)s %(process)s %(thread)s %(filename)s [%(levelname)-5.5s] %(message)s")
    # 1. file handler
    from logging.handlers import TimedRotatingFileHandler
    file_handler = TimedRotatingFileHandler('%smain.log' % log_path, when='midnight')
    file_handler.suffix = '%Y_%m_%d.log'
    file_handler.setFormatter(log_formatter)
    # 2. stream handler
    std_handler = logging.StreamHandler(sys.stdout)
    std_handler.setFormatter(log_formatter)
    logger = logging.getLogger()
    # 3. add handler
    logger.addHandler(file_handler)
    logger.addHandler(std_handler)
    logger.setLevel(level)
    logging.debug('init logging succ')


def now_ts() -> float:
    return datetime.datetime.now().timestamp()


def wrap_log_ts(func: Callable) -> None:
    @wraps(func)
    def inner(*args, **kwargs):
        ts = now_ts()
        re = func(*args, **kwargs)
        logging.info(f"{func.__name__} cost {format(now_ts()-ts, '.3f')}s")
        return re
    return inner


def wrap_log_ts_async(func: Callable) -> None:
    @wraps(func)
    async def inner(*args, **kwargs):
        ts = now_ts()
        re = await func(*args, **kwargs)
        logging.info(f"{func.__name__} cost {format(now_ts()-ts, '.3f')}s")
        return re
    return inner


def lru_pop(*arrays: list, max_length: int=10) -> None:
    for array in arrays:
        while len(array) > max_length: array.pop(0)


class IterCount(Iterator):
    def __init__(self, start: int, step: int=1) -> None:
        self.val = start
        self.step = step

    def __next__(self):
        self.val += self.step
        return self.val
    
    def __repr__(self) -> str:
        return self.val


def retry(max_retries: int=3, delay: int=2, trace_print: bool=False, is_raise=True):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"Attempt {attempt} failed: {e}")
                    if trace_print: traceback.print_exc()
                    if attempt < max_retries:
                        print(f"Waiting {delay} seconds before retrying...")
                        time.sleep(delay)
                    else:
                        print("All retries failed.")
                        if is_raise: raise
        return wrapper
    return decorator


def async_retry(max_retries: int=3, delay: int=2, trace_print: bool=False, is_raise=True):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    print(f"Attempt {attempt} failed: {e}")
                    if trace_print: traceback.print_exc()
                    if attempt < max_retries:
                        print(f"Waiting {delay} seconds before retrying...")
                        await asyncio.sleep(delay)
                    else:
                        print("All retries failed.")
                        if is_raise: raise
        return wrapper
    return decorator


def simple_template(sth: str, **kwargs) -> str:
    template = string.Template(sth)
    return template.safe_substitute(**kwargs)