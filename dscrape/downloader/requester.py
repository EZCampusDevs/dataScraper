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

import httpx

import time

import logging


class Requester:
    def __init__(self, retries=float("inf"), timeout=32) -> None:
        self.session : httpx.Client = httpx.Client()
        self.chunk_size : int = 16384

        self.headers : dict[str, str] = {}
        self.retries : int = retries
        self.timeout : int = timeout

    def request(self, method, url, **kwargs):
        response: httpx.Response = None
        tries   : int = 0
        headers : dict[str, str] = {"Accept": "*/*"}
        timeout_scale = 1
        timeout = self.timeout

        if self.headers:
            headers.update(self.headers)

        if "headers" in kwargs:
            headers.update(kwargs["headers"])
            del kwargs["headers"]

        if "timeout" in kwargs: 
            timeout = kwargs["timeout"]
            del kwargs["timeout"]

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
                    headers=headers,
                    timeout=(timeout * timeout_scale),
                    **kwargs,
                )
            except httpx.TimeoutException as exc:
                timeout_scale += 1
                logging.warning(exc)
                continue
            except httpx.ConnectError as exc:
                logging.warning(exc)
                continue

            except Exception as exc:
                logging.error(exc)
                return None

            return response
