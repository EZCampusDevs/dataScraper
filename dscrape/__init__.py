import traceback
import logging
import os
import sys
import datetime
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

from . import constants
from . import dataUtil
from . import extractor
from . import database

from py_core import logging_util



def scrape_course_information(dumper: extractor.CourseScraper, debug_break_1=False):
    try:
        dumper = dumper()

        dumper.scrape_and_dump(debug_break_1)

    except Exception as e:
        logging.error("Unknown error has occured!")
        logging.error(e)
        logging.error(traceback.format_exc())


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
    general.add_argument(
        "-l",
        "--list-scrapers",
        action="store_true",
        dest="listscrape",
        help="List the scrapers and their number.",
    )
    general.add_argument(
        "-s",
        "--scrapers",
        dest="scrape",
        help="The number to indicate which scrapers to run. Can be csv (1,2,3...), can be range, (1,2,3-5)",
    )
    general.add_argument("-p", "--password", dest="db_password", help="The database password")
    general.add_argument("-u", "--username", dest="db_username", help="The database username")
    general.add_argument("-H", "--host", dest="db_host", help="The database host")
    general.add_argument("-n", "--db_name", dest="db_name", help="The database name")
    general.add_argument("-P", "--port", dest="db_port", help="The database port")
    general.add_argument(
        "-t", "--threads", dest="threads", help="The number of extractors to run at a single time"
    )
    general.add_argument("-L", "--loglevel", dest="log_level", help=f"Set the log level, {logging_util.get_level_map_pretty()}")
    general.add_argument("-f", "--logfile", dest="log_file", help="Set the NAME of the logfile, will be put in the log directory")
    general.add_argument("-D", "--logdir", dest="log_dir", help="Set the log directroy")

    return parser.parse_args(args)


def main():
    load_dotenv()

    parsed_args = get_and_prase_args(sys.argv[1:])
    
    time = datetime.datetime.strftime( datetime.datetime.now(), "%Y-%m-%d_%H-%M-%S")
    
    log_dir = parsed_args.log_dir or os.getenv("LOG_DIR", "./logs")
    log_file = parsed_args.log_file or os.getenv("LOG_FILE", f"{constants.BRAND}{time}.log")
    log_path = os.path.join(log_dir, log_file)
    
    log_level = parsed_args.log_level or os.getenv("LOG_LEVEL", str(logging.INFO))
    log_level = dataUtil.parse_int(log_level, -1)
    
    assert log_level in logging_util.LOG_LEVEL_MAP, f"Unknown log level {log_level}"


    logging_util.setup_logging(log_file=log_path, log_level=log_level)
    logging_util.add_unhandled_exception_hook()
    
    logging.info("Starting...")
    logging.info(f"--- {constants.BRAND} ---")
    logging.info(f"--- {len(constants.BRAND) * ' '} ---")
    logging.info(f"Date Time: {time}")
    logging.info(f"Logging to {log_path}")

    if parsed_args.listscrape:

        list_extractors()

        return

    if parsed_args.db_password:
        _ = parsed_args.db_password
        parsed_args.db_password = "*" * len(_)
        logging.debug(parsed_args)
        parsed_args.db_password = _
    else:
        logging.debug(parsed_args)

    if not parsed_args.db_name:
        parsed_args.db_name = str( database.get_env_db_name("ezcampus_db"))

    if not parsed_args.db_host:
        parsed_args.db_host = str(database.get_env_db_host("localhost"))

    if not parsed_args.db_password:
        parsed_args.db_password = str(database.get_env_db_password("root"))

    if not parsed_args.db_username:
        parsed_args.db_username = str(database.get_env_db_user("test"))

    if not parsed_args.db_port:
        parsed_args.db_port = int(database.get_env_db_port(3306))

    if not parsed_args.threads:
        parsed_args.threads = 5
    elif not parsed_args.threads.isdigit():
        logging.error("Threads argument must be an integer!")
        return 1
    else:
        parsed_args.threads = int(parsed_args.threads)

        if parsed_args.threads <= 0:
            logging.error("Thread count must be larger than 0!")
            return 1

    extractors_to_use = extractor.extractors.copy()

    if parsed_args.scrape:
        index = dataUtil.parse_range_input(parsed_args.scrape)

        if not index:
            print("Could not parse any indicies. Exiting...")
            return 1

        logging.debug(f"Parsed index: {index}")

        new_extractors = [
            extractors_to_use[i] for i in index if i >= 0 and i < len(extractors_to_use)
        ]

        if len(new_extractors) != len(index):
            logging.warning("Length missmatch detected! Invalid index will be ignored.")

        extractors_to_use = new_extractors

    logging.debug(extractors_to_use)

    logging.info(f"Read hostname {parsed_args.db_host}")
    logging.info(f"Read port {parsed_args.db_port}")
    logging.info(f"Read database name {parsed_args.db_name}")
    logging.info(f"Read username {parsed_args.db_username}")
    logging.info(f"Read password {'*'*len(parsed_args.db_password)}")
    logging.info(f"Read threads {parsed_args.threads}")

    database.init_database(
        use_mysql=True,
        db_port=parsed_args.db_port,
        db_host=parsed_args.db_host,
        db_name=parsed_args.db_name,
        db_user=parsed_args.db_username,
        db_pass=parsed_args.db_password,
        create=not parsed_args.clean,
        check_env=False,
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

        try:
            database.write_scrape()
        except Exception as e:
            logging.error(e)

        ended_at = dataUtil.time_now_precise()

        elapsed = ended_at - started_at

        logging.info(f"Finished after {elapsed:.6f} seconds")


def main2():
    school = extractor.UOIT_Dumper

    school().scrape_and_dump(True)

    # for i in database.add_terms(
    #     school.school_id,
    #     [1, 2, 3, 4, 5, 6, 7],
    #     ["","","","","","","",]
    # ):
    #     print(i)
