import traceback
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

from . import dataUtil
from . import extractor
from . import database
from . import logger


def scrape_course_information(dumper: extractor.CourseScraper, debug_break_1=False):
    try:
        dumper = dumper()

        dumper.scrape_and_dump(debug_break_1)

    except Exception as e:
        logger.error("Unknown error has occured!")
        logger.error(e)
        logger.error(traceback.format_exc())


def list_extractors():

    max_width = len(str(len(extractor.extractors)))

    for i, s in enumerate(extractor.extractors):

        padding = " " * (max_width - len(str(i)))

        print(f"{padding}{i} : {s.SCHOOL_VALUE}")



def get_and_prase_args(args):
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
    general.add_argument("-l", "--list-scrapers", action="store_true",dest="listscrape", help="List the scrapers and their number.")
    general.add_argument("-s", "--scrapers", dest="scrape", help="The number to indicate which scrapers to run. Can be csv (1,2,3...), can be range, (1,2,3-5)")
    general.add_argument("-p", "--password", dest="password", help="The database password")
    general.add_argument("-u", "--username", dest="username", help="The database username")
    general.add_argument("-H", "--host", dest="host", help="The database host")
    general.add_argument("-n", "--db_name", dest="db_name", help="The database name")
    general.add_argument("-P", "--port", dest="db_port", help="The database port")
    general.add_argument("-t", "--threads", dest="threads", help="The number of extractors to run at a single time")
    return parser.parse_args(args)


def main():
    logger.create_setup_logger(log_file="logs.log")

    load_dotenv()

    parsed_args = get_and_prase_args(sys.argv[1:])

    if parsed_args.listscrape:

        list_extractors()

        return

    if parsed_args.password:
        _ = parsed_args.password
        parsed_args.password = "*" * len(_)
        logger.debug(parsed_args)
        parsed_args.password = _
    else:
        logger.debug(parsed_args)

    if not parsed_args.db_name:
        parsed_args.db_name = str(os.getenv("db_name", "hibernate_db"))

    if not parsed_args.host:
        parsed_args.host = str(os.getenv("host", "localhost"))

    if not parsed_args.password:
        parsed_args.password = str(os.getenv("password", "root"))

    if not parsed_args.username:
        parsed_args.username = str(os.getenv("username", "test"))

    if not parsed_args.db_port:
        parsed_args.db_port = int(os.getenv("db_port", 3306))

    if not parsed_args.threads:
        parsed_args.threads = 5
    elif not parsed_args.threads.isdigit():
        logger.error("Threads argument must be an integer!")
        return 1
    else:
        parsed_args.threads = int(parsed_args.threads)

        if parsed_args.threads <= 0:
            logger.error("Thread count must be larger than 0!")
            return 1


    extractors_to_use = extractor.extractors.copy()

    if parsed_args.scrape:

        index = dataUtil.parse_range_input(parsed_args.scrape)

        if not index:
            print("Could not parse any indicies. Exiting...")
            return 1

        logger.debug(f"Parsed index: {index}")

        new_extractors = [extractors_to_use[i] for i in index if i >= 0 and i < len(extractors_to_use)]

        if len(new_extractors) != len(index):
            logger.warning("Length missmatch detected! Invalid index will be ignored.")

        extractors_to_use = new_extractors

    logger.debug(extractors_to_use)

    logger.info(f"Read hostname {parsed_args.host}")
    logger.info(f"Read port {parsed_args.db_port}")
    logger.info(f"Read database name {parsed_args.db_name}")
    logger.info(f"Read username {parsed_args.username}")
    logger.info(f"Read password {'*'*len(parsed_args.password)}")
    logger.info(f"Read threads {parsed_args.threads}")

    database.init_database(
        use_mysql=True,
        database_port=parsed_args.db_port,
        database_host=parsed_args.host,
        database_name=parsed_args.db_name,
        database_user=parsed_args.username,
        database_pass=parsed_args.password,
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

        with ThreadPoolExecutor(max_workers=parsed_args.threads) as pool:
            pool.map(scrape_course_information, extractors_to_use)

    finally:
        ended_at = dataUtil.time_now_precise()

        elapsed = ended_at - started_at

        logger.info(f"Finished after {elapsed:.6f} seconds")


def main2():
    dumper = extractor.myCampus.YU_Dumper

    scrape_course_information(dumper, debug_break_1=False)
    # database.add_fac()

    #    database.drop_all()
    #
    # scrape_course_information(dumper, debug_break_1=True)
