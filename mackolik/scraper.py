"""Core scraper engine - Pro Version with enhanced anti-detection."""

import time
import logging
import random
from typing import Optional

import requests
from bs4 import BeautifulSoup

from mackolik.config import BASE_URL, HEADERS, API_HEADERS, REQUEST_TIMEOUT, REQUEST_DELAY

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
BACKOFF_BASE = 2


class MackolikScraper:
    """HTTP client with rate limiting, retry logic, and anti-detection for Mackolik."""

    def __init__(self, delay: float = REQUEST_DELAY, max_retries: int = MAX_RETRIES):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.delay = delay
        self.max_retries = max_retries
        self._last_request_time = 0.0

    def _wait(self):
        """Rate limiting with randomized delay to avoid detection."""
        elapsed = time.time() - self._last_request_time
        wait = self.delay + random.uniform(0.3, 1.2)
        if elapsed < wait:
            time.sleep(wait - elapsed)

    def get(self, url: str, params: Optional[dict] = None,
            headers: Optional[dict] = None) -> Optional[requests.Response]:
        """GET request with rate limiting, retry, and error handling."""
        full_url = url if url.startswith("http") else f"{BASE_URL}{url}"

        for attempt in range(self.max_retries):
            self._wait()
            try:
                merged_headers = {**self.session.headers, **(headers or {})}
                response = self.session.get(
                    full_url, params=params, headers=merged_headers,
                    timeout=REQUEST_TIMEOUT, allow_redirects=True,
                )
                self._last_request_time = time.time()
                response.raise_for_status()
                return response
            except requests.ConnectionError as e:
                wait_time = BACKOFF_BASE ** (attempt + 1)
                logger.warning(
                    f"Connection error for {full_url} (attempt {attempt + 1}/{self.max_retries}), "
                    f"retrying in {wait_time}s: {e}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(wait_time)
            except requests.HTTPError as e:
                status = e.response.status_code if e.response is not None else 0
                if status in (429, 500, 502, 503, 504):
                    wait_time = BACKOFF_BASE ** (attempt + 1)
                    logger.warning(
                        f"HTTP {status} for {full_url} (attempt {attempt + 1}/{self.max_retries}), "
                        f"retrying in {wait_time}s"
                    )
                    if attempt < self.max_retries - 1:
                        time.sleep(wait_time)
                elif status == 403:
                    logger.warning(f"HTTP 403 (blocked) for {full_url}")
                    return None
                else:
                    logger.error(f"HTTP {status} for {full_url}: {e}")
                    return None
            except requests.RequestException as e:
                logger.error(f"Request failed for {full_url}: {e}")
                return None

        logger.error(f"All {self.max_retries} attempts failed for {full_url}")
        return None

    def get_soup(self, url: str, params: Optional[dict] = None) -> Optional[BeautifulSoup]:
        """Fetch a page and return a BeautifulSoup object."""
        response = self.get(url, params)
        if response is None:
            return None
        return BeautifulSoup(response.text, "lxml")

    def get_json(self, url: str, params: Optional[dict] = None,
                 headers: Optional[dict] = None) -> Optional[dict]:
        """Fetch JSON data from an API endpoint."""
        merged = {**API_HEADERS, **(headers or {})}
        response = self.get(url, params, headers=merged)
        if response is None:
            return None
        try:
            return response.json()
        except ValueError as e:
            logger.error(f"Failed to parse JSON from {url}: {e}")
            return None

    def close(self):
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
