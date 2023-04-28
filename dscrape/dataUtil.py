import time
import hashlib

def time_now_int():
    return int(time.time())


def time_has_passed(x):
    return int(time.time()) > x


def parse_int(value, default=-1):

    try:
        return int(value)
    
    except ValueError:
        return default



def sha224_str(data: str):

    sha = hashlib.sha224(data.encode())

    return sha.digest()