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

import json

from bs4 import BeautifulSoup
import re
from datetime import datetime

from .common import CourseScraper

from .. import dataUtil as DU
from .. import database

import logging

"""

to check out the site for uoit use this link:
https://ssp.mycampus.ca/StudentRegistrationSsb/ssb/term/termSelection?mode=search&mepCode=UOIT

https://ssp.mycampus.ca/StudentRegistrationSsb/ssb/classSearch/get_subject?searchTerm=&term=202301&offset=1&max=10&uniqueSessionId=u4mu81683951275268&_=1683951724127
"""

MAX_COUNT = 9999999

TERM_AUTH_URL = (
    "https://{HOST}/StudentRegistrationSsb/ssb/term/termSelection?mode=search&mepCode={MEP_CODE}"
)
TERM_SEARCH_AUTH_URL = (
    "https://{HOST}/StudentRegistrationSsb/ssb/term/search?mode=search&term={TERM}"
)
TERM_SEARCH_GET_URL = "https://{HOST}/StudentRegistrationSsb/ssb/classSearch/getTerms?searchTerm=&offset=1&max={MAX_COUNT}"

TERM_SEARCH_GET_RESTRICTION = "https://{HOST}/StudentRegistrationSsb/ssb/searchResults/getRestrictions?term={TERM}&courseReferenceNumber={CRN}"

COURSE_CODES_GET_URL = "https://{HOST}/StudentRegistrationSsb/ssb/classSearch/get_subjectcoursecombo?searchTerm={SEARCH}&term={TERM_ID}&offset=1&max={MAX_COUNT}"

COURSE_DATA_GET_URL = "https://{HOST}/StudentRegistrationSsb/ssb/searchResults/searchResults?mepCode={MEP_CODE}&txt_term={TERM_ID}&txt_subjectcoursecombo={COURSE_CODES}&pageMaxSize={MAX_COUNT}"


# there is a max length URI allowed by the api,
# this keeps the number of course codes in the url to this number
# i haven't tested above 500, but my thought is upper limit of 1200 would be fine
# this would double the speed because it would half the requests, higher this is the better
# UPDATE: 1000 is too long, must be lower than that
# NOTE: url should be less than 8000 characters, otherwise server will drop it
COURSE_CODE_REQUEST_AMOUNT = 150


MATCHES_RESTRICTION_GROUP = re.compile(r"^(must|cannot)\s*be.*following\s*([^:]+):?$", re.IGNORECASE)
MATCHES_RESTRICTION_SPECIAL = re.compile(r"^special approvals:$", re.IGNORECASE)


class CourseDumper(CourseScraper):
    def __init__(
        self,
        hostname: str,
        mep_code: str,
        retries=5,
        timeout=32,
    ) -> None:
        super().__init__(retries, timeout)

        if self.SCHOOL_VALUE is None:
            raise RuntimeError("SCHOOL_VALUE was None, this is a compile error")

        self.school_id = None

        self.hostname = hostname

        self.mep_code = mep_code

        self.term_auth_url = TERM_AUTH_URL.format(HOST=self.hostname, MEP_CODE=self.mep_code)

        self.auth_timeout_seconds = 300 * 2
        self.auth_hist = {
            "terms": 0,
        }

        self.log_prefix = f"Requester {self.hostname}:"

    def auth_terms(self, force: bool = False):
        if (
            not DU.time_has_passed(self.auth_hist["terms"] + self.auth_timeout_seconds)
            and not force
        ):
            return

        logging.info(f"{self.log_prefix} Refreshing terms auth")

        self.request("get", self.term_auth_url, timeout=self.auth_timeout_seconds)

        self.auth_hist["terms"] = DU.time_now_int()

    def get_json_terms(self, max_count: int = MAX_COUNT):
        self.auth_terms()

        url = TERM_SEARCH_GET_URL.format(HOST=self.hostname, MAX_COUNT=max_count)

        r = self.request("get", url)

        if r.status_code == 200:
            return r.json()

        logging.warning(
            f"{self.log_prefix} get_json_terms got status code {r.status_code} with reason: {r.reason}"
        )
        logging.warning(r)
        logging.warning(r.text)

        return {}

    def get_json_course_codes(
        self, term_id: str, search_code: str = "", max_count: int = MAX_COUNT
    ):
        self.auth_terms()

        url = COURSE_CODES_GET_URL.format(
            HOST=self.hostname, SEARCH=search_code, TERM_ID=term_id, MAX_COUNT=max_count
        )

        r = self.request("get", url)

        if r is None:
            logging.warning(
                f"{self.log_prefix} get_json_course_codes got None response."
            )
            return {}


        if r.status_code == 200:
            return r.json()

        logging.warning(
            f"{self.log_prefix} get_json_course_codes got status code {r.status_code} with reason: {r.reason}"
        )

        return {}

    def get_json_course_data(
        self,
        term_id: str,
        course_codes: list[str] = None,
        max_count: int = MAX_COUNT,
        retry_amount=5,
    ):
        self.auth_terms()

        # api only returns at most 500 course datas
        API_COURSE_DATAS_LIMIT = 500

        retries = 0
        course_code_count = len(course_codes)
        course_code_send_amount = COURSE_CODE_REQUEST_AMOUNT

        sent_course_codes = 0

        while sent_course_codes < course_code_count:

            if retries > retry_amount:

                logging.error(f"Max retries exceeded while trying to get course_data for term {term_id}")
                
                if sublist:
                    logging.error(f"Sublist of course codes was: {sublist}")

                return {}

            sublist = course_codes[sent_course_codes : sent_course_codes + course_code_send_amount]

            if not sublist:
                logging.warning(
                    f"Course code sublist is empty??? sent_course_codes: {sent_course_codes}, course_codes_count: {course_code_count}"
                )
                retries += 1
                continue

            logging.debug(f"Fetching course datas for {len(sublist)} course codes")

            course_codes_request = "%2C".join(code.upper() for code in sublist)

            self.session.get(
                url=TERM_SEARCH_AUTH_URL.format(HOST=self.hostname, TERM=term_id),
            )

            url = COURSE_DATA_GET_URL.format(
                HOST=self.hostname,
                MEP_CODE=self.mep_code,
                TERM_ID=term_id,
                COURSE_CODES=course_codes_request,
                MAX_COUNT=max_count,
            )

            r = self.request("get", url)

            if r is None:
                logging.warning(
                    f"{self.log_prefix} get_json_course_data got None response\nRetrying..."
                )
                retries += 1
                continue

            if r.status_code != 200:
                logging.warning(
                    f"{self.log_prefix} get_json_course_data got status code {r.status_code} with reason: {r.reason}\nRetrying..."
                )
                retries += 1
                continue

            try:
                j = r.json()
            except json.JSONDecodeError as e:
                logging.warning("Did not get valid json response! Retrying...")
                retries += 1
                continue


            data = j.get("data", None)

            if not data:
                logging.warning(
                    f"Got json response for course data but no data??? {j}\nRetrying..."
                )
                retries += 1
                continue

            if len(data) >= API_COURSE_DATAS_LIMIT:
                course_code_send_amount = course_code_send_amount // 2
                logging.warning(
                    f"Got {API_COURSE_DATAS_LIMIT} course datas, which is the known api truncation point, retrying with {course_code_send_amount} course codes..."
                )

                if course_code_send_amount == 0:
                    raise Exception("course_code_send_amount has halved until 0!")

                continue

            sent_course_codes += len(sublist)

            yield j

        return {}


    def get_course_restrictions(self, term: int, crn: int) -> bytes:
        self.auth_terms()

        url = TERM_SEARCH_GET_RESTRICTION.format(HOST=self.hostname, TERM=term, CRN=crn)
        r = self.request("get", url)

        if r is None:
            logging.warning(
                f"{self.log_prefix} get_course_restrictions got None response."
            )
            return {"levels": [], "degrees": []}

        if r.status_code != 200:
            return {"levels": [], "degrees": []}

        j = r.content

        page = BeautifulSoup(j, "html.parser")
        spans = page.find_all("span")

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

            elif MATCHES_RESTRICTION_SPECIAL.match(i.text):
                s = "special"
                if s in restrictions:
                    current = restrictions[s]
                else:
                    current = []
                    restrictions[s] = current

            elif current is not None and "detail-popup-indentation" in i["class"]:
                current.append({"value": i.text, "must_be_in": must_be_in})
            else:
                if i.text == "Not all restrictions are applicable.":
                    continue
                logging.warn(f"Unknown span while parsing restrictions: {i}")

        return restrictions

    def __depricated__scrape_and_dump(self):
        print("getting terms...")
        terms = self.get_json_terms()

        with open(self.mep_code + "-terms.json", "w") as writer:
            json.dump(terms, writer, indent=3)

        term = terms[0]

        print("getting course codes (term 1 only)... ")
        course_codes = self.get_json_course_codes(term["code"], "")

        with open(self.mep_code + "-course_codes.json", "w") as writer:
            json.dump(course_codes, writer, indent=3)

        print("getting course data")
        course_data = self.get_json_course_data(term["code"])

        with open(self.mep_code + "-course_code_data.json", "w") as writer:
            json.dump(course_data, writer, indent=3)

        return

    def scrape_and_dump(self, debug_break_1=False):

        self.school_id = database.get_school_id(self.SCHOOL_VALUE, self.SUBDOMAIN, self.TIMEZONE)

        terms = self.get_json_terms()

        logging.info(f"Scraping using dumper: {self}")

        currentYear = (datetime.now().year - 1) * 100
        logging.info(f"Current term year: {currentYear}")

        real_term_id_and_desc = list(
            filter(
                lambda x: int(x[0]) >= currentYear, [(i["code"], i["description"]) for i in terms]
            )
        )

        real_term_id = [i[0] for i in real_term_id_and_desc]
        term_desc = [i[1] for i in real_term_id_and_desc]

        internal_term_ids = database.add_terms(self.school_id, real_term_id, term_desc)

        logging.info(f"Found term {real_term_id}")

        for real_id, internal_id in zip(real_term_id, internal_term_ids):
            logging.info(f"Fetching term {real_id}")
            course_codes = self.get_json_course_codes(real_id, "")

            course_code = [i["code"] for i in course_codes]
            course_desc = [i["description"] for i in course_codes]

            logging.debug(f"Got course codes {course_code}")

            i = database.add_courses(
                [internal_id for i in range(len(course_desc))], course_code, course_desc
            )

            logging.info(f"Fetching course data for term and {len(course_code)} courses")
            for course_data in self.get_json_course_data(real_id, course_code):
                if not course_data:
                    logging.info("Could not get course data")
                    continue

                course_data = course_data["data"]
                course_data_str = str(course_data)[0:200]
                logging.debug(f"Course data gotten: {course_data_str}")

                # NOTE: assuming course_code and i are in order (they should be), this works fine
                #       otherwise we probably need to query the db for every course data we insert
                course_id_map = {course_code: j for course_code, j in zip(course_code, i)}
                proper_course_id = [course_id_map[i["subjectCourse"]] for i in course_data]
                # restrictions = [dumper.get_course_restrictions(id, i['courseReferenceNumber']) for i in course_data]

                logging.info(
                    f"proper_course_id length = {len(proper_course_id)}, course_data length = {len(course_data)}"
                )

                # with open("debug1.json", "w")as writer:
                #     json.dump(proper_course_id, writer, indent=3)

                database.add_course_data(self.school_id, proper_course_id, course_data)
                # database.add_course_data(proper_course_id, course_data, restrictions)

            if debug_break_1:
                logging.error("DEBUG BREAK")
                return


class UOIT_Dumper(CourseDumper):
    SCHOOL_VALUE = "Ontario Tech University - Canada"
    SUBDOMAIN = "otu"
    TIMEZONE = "America/Toronto"

    def __init__(self, retries=float("inf"), timeout=4*32) -> None:
        super().__init__("ssp.mycampus.ca", "UOIT", retries, timeout)


class UVIC_Dumper(CourseDumper):
    SCHOOL_VALUE = "University of Victoria - Canada"
    SUBDOMAIN = "uv"
    TIMEZONE = "America/Vancouver"

    def __init__(self, retries=float("inf"), timeout=32) -> None:
        super().__init__("banner.uvic.ca", "UVIC", retries, timeout)


class DC_Dumper(CourseDumper):
    SCHOOL_VALUE = "Durham College - Canada"
    SUBDOMAIN = "dc"
    TIMEZONE = "America/Toronto"

    def __init__(self, retries=float("inf"), timeout=32) -> None:
        super().__init__("ssp.mycampus.ca", "DC", retries, timeout)


class TTU_Dumper(CourseDumper):
    SCHOOL_VALUE = "Texas Tech University - USA"
    SUBDOMAIN = "ttu"
    TIMEZONE = "America/Chicago"

    def __init__(self, retries=float("inf"), timeout=32) -> None:
        super().__init__("registration.texastech.edu", "TTU", retries, timeout)


class RDP_Dumper(CourseDumper):
    SCHOOL_VALUE = "Red Deer Polytechnic - Canada"
    SUBDOMAIN = "rdp"
    TIMEZONE = "America/Edmonton"

    def __init__(self, retries=float("inf"), timeout=32) -> None:
        super().__init__("myinfo.rdc.ab.ca", "", retries, timeout)


class OC_Dumper(CourseDumper):
    SCHOOL_VALUE = "Okanagan College - Canada"
    SUBDOMAIN = "oc"
    TIMEZONE = "America/Vancouver"

    def __init__(self, retries=float("inf"), timeout=32) -> None:
        super().__init__("selfservice.okanagan.bc.ca", "", retries, timeout)


class TRU_Dumper(CourseDumper):

    """
    Seems to have issues with 400 errors sometimes
    """

    SCHOOL_VALUE = "Thompson Rivers University - Canada"
    SUBDOMAIN = "tru"
    TIMEZONE = "America/Vancouver"

    def __init__(self, retries=float("inf"), timeout=32) -> None:
        super().__init__("reg-prod.ec.tru.ca", "", retries, timeout)


class KPU_Dumper(CourseDumper):
    SCHOOL_VALUE = "Kwantlen Polytechnic University - Canada"
    SUBDOMAIN = "kpu"
    TIMEZONE = "America/Vancouver"

    def __init__(self, retries=float("inf"), timeout=32) -> None:
        super().__init__("banweb3.kpu.ca", "", retries, timeout)


class UOS_Dumper(CourseDumper):
    SCHOOL_VALUE = "University of Saskatchewan - Canada"
    SUBDOMAIN = "uos"
    TIMEZONE = "America/Regina"

    def __init__(self, retries=float("inf"), timeout=32) -> None:
        super().__init__("banner.usask.ca", "", retries, timeout)


class YU_Dumper(CourseDumper):
    SCHOOL_VALUE = "Yukon University - Canada"
    SUBDOMAIN = "yu"
    TIMEZONE = "America/Whitehorse"

    def __init__(self, retries=float("inf"), timeout=32) -> None:
        super().__init__("banner.yukonu.ca", "", retries, timeout)
