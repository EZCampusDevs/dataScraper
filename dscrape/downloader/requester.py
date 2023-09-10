# Copyright (C) 2022-2023 EZCampus 
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import requests
from requests.exceptions import RequestException, ConnectionError, Timeout

import time

import logging


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

                logging.debug(f"Retrying {method} to {url} after {tries} seconds")

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
                logging.warning(exc)
                continue

            except Exception as exc:
                logging.error(exc)
                return None

            return response
