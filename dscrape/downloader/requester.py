import requests
from requests.exceptions import RequestException, ConnectionError, Timeout

import time

from .. import logger


class Requester:
    def __init__(self, retries=float("inf"), timeout=32) -> None:
        self.session = requests.Session()
        self.chunk_size = 16384

        self.headers = {}
        self.retries = retries
        self.timeout = timeout

    def request(self, method, url, **kwargs):
        response: requests.Response = None
        tries = 0
        headers = {"Accept": "*/*"}

        if self.headers:
            headers.update(self.headers)

        if "headers" in kwargs:
            headers.update(kwargs["headers"])

        while True:
            if tries > 0:
                if response:
                    response.close()
                    response = None

                if tries > self.retries:
                    return None

                logger.debug(f"Retrying {method} to {url} after {tries} seconds")

                time.sleep(tries)

            try:
                response = self.session.request(
                    method,
                    url,
                    stream=True,
                    headers=headers,
                    timeout=self.timeout,
                    **kwargs,
                )
            except (ConnectionError, Timeout) as exc:
                logger.warning(exc)
                continue

            except Exception as exc:
                logger.error(exc)
                return None

            return response
