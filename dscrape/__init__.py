
from datetime import datetime

from concurrent.futures import ThreadPoolExecutor


from . import extractor
from . import database
from . import logger


def scrape_course_information(dumper):

    dumper = dumper()

    terms = dumper.get_json_terms()

    logger.info(f"Scraping using dumper: {dumper}")

    term_id = [i["code"] for i in terms]
    term_desc = [i["description"] for i in terms]

    logger.info(f"Found term {term_id}")

    database.add_terms(term_id, term_desc)

    currentYear = (datetime.now().year - 1) * 100
    logger.info(f"Current term year: {currentYear}")


    for id in term_id:
        if int(id) < currentYear:
            logger.info(f"Skipping term {id} because it should be out of date")
            continue

        logger.info(f"Fetching term {id}")
        course_codes = dumper.get_json_course_codes(id, "")

        course_code = [i["code"] for i in course_codes]
        course_desc = [i["description"] for i in course_codes]

        i = database.add_courses(
            [id for i in range(len(course_desc))], course_code, course_desc
        )

        logger.info(f"Fetching course data for term and {len(course_code)} courses")
        course_data = dumper.get_json_course_data(id, course_code)

        if not course_data:
            logger.info("Could not get course data")
            continue

        course_data = course_data["data"]

        database.add_course_data(i, course_data)

def main():
    
    logger.create_setup_logger()

    database.init_database("myCampus.sqlite3", "./")

    # main2()
    # return
    with ThreadPoolExecutor(max_workers=5) as pool:

        pool.map(scrape_course_information, extractor.extractors)

 
def main2():
    
    dumper = extractor.myCampus.UOIT_Dumper()

    terms = dumper.get_json_terms()

    logger.info(f"Scraping using dumper: {dumper}")

    term_id = [i["code"] for i in terms]
    term_desc = [i["description"] for i in terms]

    logger.info(f"Found term {term_id}")

    database.add_terms(term_id, term_desc)

    currentYear = (datetime.now().year - 1) * 100
    logger.info(f"Current term year: {currentYear}")


    for id in term_id:
        if int(id) < currentYear:
            logger.info(f"Skipping term {id} because it should be out of date")
            continue

        logger.info(f"Fetching term {id}")
        course_codes = dumper.get_json_course_codes(id, "")

        course_code = [i["code"] for i in course_codes]
        course_desc = [i["description"] for i in course_codes]

        i = database.add_courses(
            [id for i in range(len(course_desc))], course_code, course_desc
        )

        logger.info(f"Fetching course data for term and {len(course_code)} courses")
        course_data = dumper.get_json_course_data(id, course_code)

        if not course_data:
            logger.info("Could not get course data")
            continue

        course_data = course_data["data"]

        database.add_course_data(i, course_data)
        break 