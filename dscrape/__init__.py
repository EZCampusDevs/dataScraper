import traceback
from datetime import datetime

from concurrent.futures import ThreadPoolExecutor

from . import dataUtil
from . import extractor
from . import database
from . import logger


def scrape_course_information(dumper, debug_break_1=False):
    try:
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

            logger.debug(f"Got course codes {course_code}")

            i = database.add_courses(
                [id for i in range(len(course_desc))], course_code, course_desc
            )

            logger.info(f"Fetching course data for term and {len(course_code)} courses")
            for course_data in dumper.get_json_course_data(id, course_code):
                if not course_data:
                    logger.info("Could not get course data")
                    continue

                course_data = course_data["data"]
                course_data_str = str(course_data)[0:200]
                logger.debug(f"Course data gotten: {course_data_str}")
                database.add_course_data(i, course_data)

            if debug_break_1:
                logger.error("DEBUG BREAK")
                return

    except Exception as e:
        logger.error("Unknown error has occured!")
        logger.error(e)
        logger.error(traceback.format_exc())
        


def main():
    logger.create_setup_logger(log_file="logs.log")

    database.init_database(
        use_mysql=True,
        database_host="localhost",
        database_name="hibernate_db",
        database_user="test",
        database_pass="root"
    )

    started_at = dataUtil.time_now_precise()
    try:
        # main2()
        # return

        with ThreadPoolExecutor(max_workers=5) as pool:
            pool.map(scrape_course_information, extractor.extractors)

    finally:
        ended_at = dataUtil.time_now_precise()

        elapsed = ended_at - started_at

        logger.info(f"Finished after {elapsed:.6f} seconds")


def main2():
    dumper = extractor.myCampus.UOIT_Dumper

    # database.add_fac()

    scrape_course_information(dumper, debug_break_1=True)
