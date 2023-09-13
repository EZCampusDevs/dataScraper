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

from bs4 import BeautifulSoup
import re

"""


DEBUG IGNORE THIS




"""
with open("debug.html", "rb") as reader:
    page = reader.read()


page = BeautifulSoup(page, "html.parser")


spans = page.find_all("span")


MATCHES_LEVELS = re.compile("^must\s*be.*following\s*levels:?$", re.IGNORECASE)
MATCHES_DEGREE = re.compile("^must\s*be.*following\s*degrees:?$", re.IGNORECASE)

MATCHES_RESTRICTION_GROUP = re.compile("^(must|cannot)\s*be.*following\s*([^:]+):?$", re.IGNORECASE)
MATCHES_RESTRICTION_SPECIAL = re.compile("^special approvals:$", re.IGNORECASE)


restrictions = {}
current = None
must_be_in = False
for i in spans:
    m = MATCHES_RESTRICTION_GROUP.match(i.text)

    if m:
        must_be_in = m.group(1).lower() == "must"
        group = m.group(2).lower()

        if group in restrictions:
            current = restrictions[group]

        else:
            current = []
            restrictions[group] = current

        continue

    elif MATCHES_RESTRICTION_SPECIAL.match(i.text):
        s = "special"
        if s in restrictions:
            current = restrictions[s]
        else:
            current = []
            restrictions[s] = current
        continue

    elif current is not None and "detail-popup-indentation" in i["class"]:
        current.append({"value": i.text, "must_be_in": must_be_in})
    else:
        print("UNKNOWN VALUE")

print(restrictions)
