import json

from bs4 import BeautifulSoup
import re

from ..downloader import requester
from .. import dataUtil as DU
from .. import logger


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
            return {
                "levels" : [],
                "degrees" : []
            }

        j = r.content

        page = BeautifulSoup(j, "html.parser")
        spans = page.find_all("span")

        
        restrictions ={}
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
                current.append({
                    "value": i.text,
                    "must_be_in" : must_be_in })
            else:
                if i.text == "Not all restrictions are applicable.":
                    continue
                logger.warn(f"Unknown span while parsing restrictions: {i}")

        return restrictions 

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

        return

    """
    def __get_str_course_restrictions(self, crn: int) -> str:
        if not isinstance(crn, int):
            raise TypeError(f"crn expected {int}, received {type(crn)}")

        session = requests.Session()

        session.get(
            url=f"https://{self.__domain}/StudentRegistrationSsb/ssb/term"
                f"/termSelection?mode=search&mepCode={self.__mep_code}",
            timeout=5
        )

        return session.get(
            url=f"https://{self.__domain}/StudentRegistrationSsb/ssb"
                f"/searchResults/getRestrictions?term={self.__term_id}"
                f"&courseReferenceNumber={crn}",
            timeout=5
        ).text
    def __decode_str_course_restrictions(self, html_text: str) -> dict:
        html_cleaned_up_lines = re.findall(r"<span class=(.*?)</span>",
                                           html_text)

        restrictions = {}

        for line in html_cleaned_up_lines:
            line = self.__general_str_cleanup(line)

            if "not all restrictions are applicable" in line.lower():
                # Restrictions we specifically don't care about.
                pass

            elif "\"status-bold\">" in line:
                # "\"status-bold\">" Is like the title header.
                # Example: "Cannot be enrolled in one of the following Majors:".
                restrictions[line.replace("\"status-bold\">", "")] = []
                # Removed header and add line as a dict key with a value of [].

            elif "\"detail-popup-indentation\">" in line:
                # "\"detail-popup-indentation\">" Is like the detail header.
                # For example: "Biological Science (BIOL)".
                restrictions[list(restrictions.keys())[-1]].append(
                    line.replace("\"detail-popup-indentation\">", "")
                )
                # Removed header and add cleaned up line to the last dict key.

        return restrictions

"""


class UOIT_Dumper(CourseDumper):
    def __init__(self, retries=float("inf"), timeout=32) -> None:
        super().__init__("ssp.mycampus.ca", "UOIT", retries, timeout)


class UVIC_Dumper(CourseDumper):
    def __init__(self, retries=float("inf"), timeout=32) -> None:
        super().__init__("banner.uvic.ca", "UVIC", retries, timeout)
