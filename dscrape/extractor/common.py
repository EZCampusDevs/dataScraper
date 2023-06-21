from ..downloader import requester


class CourseScraper(requester.Requester):
    """
    Base class for all course scrapers
    """

    SCHOOL_VALUE = None
    SUBDOMAIN = None

    def scrape_and_dump(self, debug_break_1: bool = False):
        """
        Fetches all the data the current scraper can get and writes it to the database
        """
        raise RuntimeError("CourseScraper.scrape_and_dump is abstract and cannot be called")
