"""Core scraper engine for Maçkolik."""

import time
import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup

from mackolik.config import BASE_URL, HEADERS, REQUEST_TIMEOUT, REQUEST_DELAY

logger = logging.getLogger(__name__)


class MackolikScraper:
    """HTTP client with rate limiting and retry logic for Maçkolik."""

    def __init__(self, delay: float = REQUEST_DELAY):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.delay = delay
        self._last_request_time = 0.0

    def _wait(self):
        """Respect rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)

    def get(self, url: str, params: Optional[dict] = None) -> Optional[requests.Response]:
        """Make a GET request with rate limiting and error handling."""
        self._wait()
        full_url = url if url.startswith("http") else f"{BASE_URL}{url}"
        try:
            response = self.session.get(full_url, params=params, timeout=REQUEST_TIMEOUT)
            self._last_request_time = time.time()
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"Request failed for {full_url}: {e}")
            return None

    def get_soup(self, url: str, params: Optional[dict] = None) -> Optional[BeautifulSoup]:
        """Fetch a page and return a BeautifulSoup object."""
        response = self.get(url, params)
        if response is None:
            return None
        return BeautifulSoup(response.text, "lxml")

    def get_json(self, url: str, params: Optional[dict] = None) -> Optional[dict]:
        """Fetch JSON data from an API endpoint."""
        response = self.get(url, params)
        if response is None:
            return None
        try:
            return response.json()
        except ValueError as e:
            logger.error(f"Failed to parse JSON from {url}: {e}")
            return None

    def close(self):
        """Close the session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
