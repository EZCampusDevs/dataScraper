import json

from bs4 import BeautifulSoup
import re
from datetime import datetime

from .common import CourseScraper

from .. import dataUtil as DU
from .. import logger
from .. import database


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
COURSE_CODE_REQUEST_AMOUNT = 700


MATCHES_RESTRICTION_GROUP = re.compile("^(must|cannot)\s*be.*following\s*([^:]+):?$", re.IGNORECASE)
MATCHES_RESTRICTION_SPECIAL = re.compile("^special approvals:$", re.IGNORECASE)


class CourseDumper(CourseScraper):
    def __init__(
        self,
        school_value: str,
        hostname: str,
        mep_code: str,
        retries=float("inf"),
        timeout=32,
    ) -> None:
        super().__init__(retries, timeout)

        self.school_id = database.get_school_id(school_value)

        self.hostname = hostname

        self.mep_code = mep_code

        self.term_auth_url = TERM_AUTH_URL.format(HOST=self.hostname, MEP_CODE=self.mep_code)

        self.auth_timeout_seconds = 60
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

        logger.info(f"{self.log_prefix} Refreshing terms auth")

        self.session.get(self.term_auth_url, timeout=self.auth_timeout_seconds)

        self.auth_hist["terms"] = DU.time_now_int()

    def get_json_terms(self, max_count: int = MAX_COUNT):
        self.auth_terms()

        url = TERM_SEARCH_GET_URL.format(HOST=self.hostname, MAX_COUNT=max_count)

        r = self.request("get", url)

        if r.status_code == 200:
            return r.json()

        logger.warning(
            f"{self.log_prefix} get_json_terms got status code {r.status_code} with reason: {r.reason}"
        )
        logger.warning(r)
        logger.warning(r.text)

        return {}

    def get_json_course_codes(
        self, term_id: str, search_code: str = "", max_count: int = MAX_COUNT
    ):
        self.auth_terms()

        url = COURSE_CODES_GET_URL.format(
            HOST=self.hostname, SEARCH=search_code, TERM_ID=term_id, MAX_COUNT=max_count
        )
        r = self.request("get", url)

        if r.status_code == 200:
            return r.json()

        logger.warning(
            f"{self.log_prefix} get_json_course_codes got status code {r.status_code} with reason: {r.reason}"
        )

        return {}

    def get_json_course_data(
        self, term_id: str, course_codes: list[str] = None, max_count: int = MAX_COUNT
    ):
        self.auth_terms()

        course_code_count = COURSE_CODE_REQUEST_AMOUNT
        for i in range(0, len(course_codes), course_code_count):
            sublist = course_codes[i : i + course_code_count]

            if sublist:
                course_code_list = [code.upper() for code in sublist]
                course_codes_request = "%2C".join(course_code_list)

            else:
                continue

            self.session.get(
                url=TERM_SEARCH_AUTH_URL.format(HOST=self.hostname, TERM=term_id),
                timeout=5,
            )

            url = COURSE_DATA_GET_URL.format(
                HOST=self.hostname,
                MEP_CODE=self.mep_code,
                TERM_ID=term_id,
                COURSE_CODES=course_codes_request,
                MAX_COUNT=max_count,
            )

            r = self.request("get", url)

            if r.status_code == 200:
                j = r.json()

                yield j
                continue

            logger.warning(
                f"{self.log_prefix} get_json_course_data got status code {r.status_code} with reason: {r.reason}"
            )
            continue

        return {}

    def get_course_restrictions(self, term: int, crn: int) -> bytes:
        self.auth_terms()

        url = TERM_SEARCH_GET_RESTRICTION.format(HOST=self.hostname, TERM=term, CRN=crn)
        r = self.request("get", url)

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
                logger.warn(f"Unknown span while parsing restrictions: {i}")

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
        terms = self.get_json_terms()

        logger.info(f"Scraping using dumper: {self}")

        term_id = [i["code"] for i in terms]
        term_desc = [i["description"] for i in terms]

        logger.info(f"Found term {term_id}")

        database.add_terms(self.school_id, term_id, term_desc)

        currentYear = (datetime.now().year - 1) * 100
        logger.info(f"Current term year: {currentYear}")

        for id in term_id:
            if int(id) < currentYear:
                logger.info(f"Skipping term {id} because it should be out of date")
                continue

            logger.info(f"Fetching term {id}")
            course_codes = self.get_json_course_codes(id, "")

            course_code = [i["code"] for i in course_codes]
            course_desc = [i["description"] for i in course_codes]

            logger.debug(f"Got course codes {course_code}")

            i = database.add_courses(
                [id for i in range(len(course_desc))], course_code, course_desc
            )

            logger.info(f"Fetching course data for term and {len(course_code)} courses")
            for course_data in self.get_json_course_data(id, course_code):
                if not course_data:
                    logger.info("Could not get course data")
                    continue

                course_data = course_data["data"]
                course_data_str = str(course_data)[0:200]
                logger.debug(f"Course data gotten: {course_data_str}")

                # NOTE: assuming course_code and i are in order (they should be), this works fine
                #       otherwise we probably need to query the db for every course data we insert
                course_id_map = {course_code: j for course_code, j in zip(course_code, i)}
                proper_course_id = [course_id_map[i["subjectCourse"]] for i in course_data]
                # restrictions = [dumper.get_course_restrictions(id, i['courseReferenceNumber']) for i in course_data]

                logger.info(
                    f"proper_course_id length = {len(proper_course_id)}, course_data length = {len(course_data)}"
                )

                # with open("debug1.json", "w")as writer:
                #     json.dump(proper_course_id, writer, indent=3)

                database.add_course_data(self.school_id, proper_course_id, course_data)
                # database.add_course_data(proper_course_id, course_data, restrictions)

            if debug_break_1:
                logger.error("DEBUG BREAK")
                return


class UOIT_Dumper(CourseDumper):
    def __init__(self, retries=float("inf"), timeout=32) -> None:
        super().__init__(
            "Ontario Tech University - Canada", "ssp.mycampus.ca", "UOIT", retries, timeout
        )


class UVIC_Dumper(CourseDumper):
    def __init__(self, retries=float("inf"), timeout=32) -> None:
        super().__init__(
            "University of Victory - Canada", "banner.uvic.ca", "UVIC", retries, timeout
        )
