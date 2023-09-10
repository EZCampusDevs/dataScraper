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

BRAND = "SchedulePlatform-DataScrape"


# used to represent days of the week in a single integer
# example:
# 2 has a value of 0010 in binary
# so it would be Tuesday
# 3 has a value of 0011 in binary
# so it wold be Monday, Tuesday
#
MONDAY = 0b000_0001
TUESDAY = 0b000_0010
WEDNESDAY = 0b000_0100
THURSDAY = 0b000_1000
FRIDAY = 0b001_0000
SATURDAY = 0b010_0000
SUNDAY = 0b100_0000
