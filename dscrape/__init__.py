import traceback
import sys
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

                # NOTE: assuming course_code and i are in order (they should be), this works fine
                #       otherwise we probably need to query the db for every course data we insert
                course_id_map = {course_code: j for course_code, j in zip(course_code, i)}
                proper_course_id = [course_id_map[i["subjectCourse"]] for i in course_data]

                logger.info(
                    f"proper_course_id length = {len(proper_course_id)}, course_data length = {len(course_data)}"
                )

                # with open("debug1.json", "w")as writer:
                #     json.dump(proper_course_id, writer, indent=3)

                database.add_course_data(proper_course_id, course_data)

            if debug_break_1:
                logger.error("DEBUG BREAK")
                return

    except Exception as e:
        logger.error("Unknown error has occured!")
        logger.error(e)
        logger.error(traceback.format_exc())


def parse_args(args):
    import argparse

    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTION]...",
        add_help=False,
    )

    general = parser.add_argument_group("General Options")
    general.add_argument(
        "-h",
        "--help",
        action="help",
        help="Print this help message and exit",
    )
    general.add_argument(
        "-c", "--clean", dest="clean", action="store_true", help="Delete the entire database"
    )
    general.add_argument(
        "-d", "--debug", dest="debug", action="store_true", help="Run the debug main method"
    )
    return parser.parse_args(args)


def main():
    logger.create_setup_logger(log_file="logs.log")

    parsed_args = parse_args(sys.argv[1:])

    logger.debug(parsed_args)

    database.init_database(
        use_mysql=True,
        database_host="localhost",
        database_name="hibernate_db",
        database_user="test",
        database_pass="root",
        create=not parsed_args.clean,
    )

    if parsed_args.clean:
        if dataUtil.ask_for_confirmation("Are you sure you want to delete the entire database? "):
            database.drop_all()
        return

    started_at = dataUtil.time_now_precise()
    try:
        database.get_current_scrape()

        if parsed_args.debug:
            main2()
            return

        with ThreadPoolExecutor(max_workers=5) as pool:
            pool.map(scrape_course_information, extractor.extractors)

    finally:
        ended_at = dataUtil.time_now_precise()

        elapsed = ended_at - started_at

        logger.info(f"Finished after {elapsed:.6f} seconds")


def main2():
    dumper = extractor.myCampus.UOIT_Dumper
    d_instance = dumper()

    terms = d_instance.get_json_terms()
    term_id = [i["code"] for i in terms]
    term_id = term_id[0]

    logger.debug(term_id)
    course_codes = d_instance.get_json_course_codes(term_id)

    course_code = [i["code"] for i in course_codes]

    for course_data in d_instance.get_json_course_data(term_id, course_code):
        # logger.debug(course_data)

        course_data = course_data["data"]

        for course in course_data:


            crn = course["courseReferenceNumber"]
            text = d_instance.get_course_restrictions(term_id, crn)

            logger.info(text)

        return

    # database.add_fac()

    #    database.drop_all()
    #
    scrape_course_information(dumper, debug_break_1=True)
