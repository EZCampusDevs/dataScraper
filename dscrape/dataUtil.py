import re 
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


def ask_for_confirmation(prompt: str):
    while True:
        i = input(prompt + " (y/n): ")

        if i in ("yes", "y", "confirm"):
            return True
        elif i in ("no", "n", "deny"):
            return False


def replace_bad_escapes(value):
    value = value.replace("&amp;", "&").replace("&#39;", "'")

    return value


def parse_range_input(value:str):
    """
    Parses a csv of numbers and ranges

    1,2,3,4 -> (1, 2, 3, 4)
    1-5,8   -> (1, 2, 3, 4, 5, 8)
    """

    output_nums = set()

    values = value.split(",")

    REGEX = re.compile(r"(\d+\s*\-\s*\d+)|(\d+)")

    for value in values:

        m = REGEX.match(value.strip())

        if not m:
            continue

        range_pred = m.group(1)
        single_num = m.group(2)

        if range_pred:

            _ = [int(i.strip()) for i in range_pred.split("-")]

            start, stop = _

            if start > stop:
                start, stop = stop, start

            stop += 1

            for i in range(start, stop):
                output_nums.add(i)

        if single_num:

            _ = int(single_num.strip())

            output_nums.add(_)

    return tuple(output_nums)