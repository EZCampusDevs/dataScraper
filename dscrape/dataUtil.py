import time


def time_now_int():
    return int(time.time())


def time_has_passed(x):
    return int(time.time()) > x
