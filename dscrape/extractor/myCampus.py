import json

from ..downloader import requester
from .. import dataUtil as DU
from .. import logger


MAX_COUNT = 9999999

TERM_AUTH_URL = (
    "https://{HOST}/StudentRegistrationSsb/ssb/term/termSelection?mode=search&mepCode={MEP_CODE}"
)
TERM_SEARCH_AUTH_URL = (
    "https://{HOST}/StudentRegistrationSsb/ssb/term/search?mode=search&term={TERM}"
)
TERM_SEARCH_GET_URL = "https://{HOST}/StudentRegistrationSsb/ssb/classSearch/getTerms?searchTerm=&offset=1&max={MAX_COUNT}"

COURSE_CODES_GET_URL = "https://{HOST}/StudentRegistrationSsb/ssb/classSearch/get_subjectcoursecombo?searchTerm={SEARCH}&term={TERM_ID}&offset=1&max={MAX_COUNT}"

COURSE_DATA_GET_URL = "https://{HOST}/StudentRegistrationSsb/ssb/searchResults/searchResults?mepCode={MEP_CODE}&txt_term={TERM_ID}&txt_subjectcoursecombo={COURSE_CODES}&pageMaxSize={MAX_COUNT}"


# there is a max length URI allowed by the api,
# this keeps the number of course codes in the url to this number
# i haven't tested above 500, but my thought is upper limit of 1200 would be fine
# this would double the speed because it would half the requests, higher this is the better
COURSE_CODE_REQUEST_AMOUNT = 1000


class CourseDumper(requester.Requester):
    def __init__(
        self,
        hostname: str,
        mep_code: str,
        retries=float("inf"),
        timeout=32,
    ) -> None:
        super().__init__(retries, timeout)

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

    def get_json_course_codes(self, term_id: str, search_code: str, max_count: int = MAX_COUNT):
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

    def scrape_and_dump(self):
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


class UOIT_Dumper(CourseDumper):
    def __init__(self, retries=float("inf"), timeout=32) -> None:
        super().__init__("ssp.mycampus.ca", "UOIT", retries, timeout)


class UVIC_Dumper(CourseDumper):
    def __init__(self, retries=float("inf"), timeout=32) -> None:
        super().__init__("banner.uvic.ca", "UVIC", retries, timeout)
