# Copyright (C) 2022-2023 EZCampus 
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import re
import time
import hashlib
import traceback
from datetime import datetime

import dateutil.parser as datePasrer


from . import constants
import logging


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
        logging.error(e)
        logging.error(traceback.format_exc())

        raise e


def ask_for_confirmation(prompt: str):
    while True:
        i = input(prompt + " (y/n): ")

        if i in ("yes", "y", "confirm"):
            return True
        elif i in ("no", "n", "deny"):
            return False


def replace_bad_escapes(value):
    if value is None:
        return

    return value.replace("&amp;", "&").replace("&#39;", "'")


def parse_range_input(value: str):
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
