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

from .common import CourseScraper
from .myCampus import (
    UOIT_Dumper,
    UVIC_Dumper,
    TTU_Dumper,
    DC_Dumper,
    RDP_Dumper,
    OC_Dumper,
    TRU_Dumper,
    KPU_Dumper,
    UOS_Dumper,
    YU_Dumper,
)

extractors = [
    UOIT_Dumper,
    UVIC_Dumper,
    TTU_Dumper,
    DC_Dumper,
    RDP_Dumper,
    OC_Dumper,
    TRU_Dumper,
    KPU_Dumper,
    UOS_Dumper,
    YU_Dumper,
]
