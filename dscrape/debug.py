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
