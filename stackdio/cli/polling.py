
import time
from functools import wraps

import click


class TimeoutException(Exception):
    pass


def poll_and_wait(func):
    """
    Execute func in increments of sleep_time for no more than max_time.
    Raise TimeoutException if we're not successful in max_time
    """
    @wraps(func)
    def decorator(args=None, sleep_time=2, max_time=120):
        args = args or []

        current_time = 0

        success = func(*args)
        while not success and current_time < max_time:
            current_time += sleep_time
            time.sleep(sleep_time)
            click.echo('.', nl=False)
            success = func(*args)

        if not success:
            raise TimeoutException()

    return decorator
