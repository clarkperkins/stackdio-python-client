
import sys
import time


class TimeoutException(Exception):
    pass


def poll_and_wait(func, args=None, sleep_time=2, max_time=120):
    """Execute func in increments of sleep_time for no more than max_time.
    Raise TimeoutException if we're not successful in max_time"""
    #pylint: disable=W0142

    args = args or []
    current_time = 0

    success = func(*args)
    while not success and current_time < max_time:
        sys.stdout.write(".")
        sys.stdout.flush()
        current_time += sleep_time
        time.sleep(sleep_time)
        success = func(*args)

    if not success:
        raise TimeoutException()

