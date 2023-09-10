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


def parse_range_input(value: str):
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


values = [
    "1,2,3,4,5",
    "1-2,3,4,5",
    "1,2-3,4,5",
    "1,2-3,4-5",
    "1-2",
    "1 ,2-3,4-5",
    "1 , 2- 3, 4-5",
    "12, 12- 3, 4-5",
    "a12, 12- 3 4-5",
    "12-2-3 4-5",
]
for i in values:
    parse_range_input(i)
