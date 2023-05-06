import time
import hashlib
import traceback
from datetime import datetime 

import dateutil.parser as datePasrer


from . import constants
from . import logger

def time_now_precise():
    return time.perf_counter()


def time_now_int():
    return int(time.time())


def time_has_passed(x):
    return int(time.time()) > x


def parse_int(value, default=-1):
    try:
        return int(value)

    except ValueError:
        return default


def sha256_of_str(data: str):
    sha = hashlib.sha256(data.encode())

    return sha.digest()


def get_weekdays_int(data: dict[str, bool]):
    value = 0

    if data.get("monday", False):
        value |= constants.MONDAY

    if data.get("tuesday", False):
        value |= constants.TUESDAY

    if data.get("wednesday", False):
        value |= constants.WEDNESDAY

    if data.get("thursday", False):
        value |= constants.THURSDAY

    if data.get("friday", False):
        value |= constants.FRIDAY

    if data.get("saturday", False):
        value |= constants.SATURDAY

    if data.get("sunday", False):
        value |= constants.SUNDAY

    return value


def get_weekdays_int_bad(data: dict[str, bool]):
    value = 0

    for key, value in data.items():
        if not value or not isinstance(key, str):
            continue

        l_key = key.lower()

        if l_key in ("mon", "monday"):
            value |= constants.MONDAY

        elif l_key in ("tue", "tuesday"):
            value |= constants.TUESDAY

        elif l_key in ("wed", "wednesday"):
            value |= constants.WEDNESDAY

        elif l_key in ("thu", "thursday"):
            value |= constants.THURSDAY

        elif l_key in ("fri", "friday"):
            value |= constants.FRIDAY

        elif l_key in ("sat", "saturday"):
            value |= constants.SATURDAY

        elif l_key in ("sun", "sunday"):
            value |= constants.SUNDAY

    return value




def parse_date(date: str):

    try: 
        return datetime.strptime(date, "%m/%d/%Y").date() 
    except ValueError:
        pass  

    try: 
        return datetime.strptime(date, "%b %d, %Y").date() 
    except ValueError:
        pass  

    try:
        return datePasrer.parse(date).date()

    except Exception as e:
        logger.error(e)
        logger.error(traceback.format_exc())
        
        raise e


