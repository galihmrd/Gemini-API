import requests
import re
import random
import string
import json
import urllib.parse
from typing import Optional, Tuple, Dict, Any
from requests.exceptions import RequestException

from .constants import HEADERS, HOST, BOT_SERVER, POST_ENDPOINT


class Gemini:
    def __init__(self, cookies: Optional[Dict[str, str]] = None) -> None:
        self.session: requests.Session = requests.Session()
        self.base_url: str = HOST
        self.session.headers.update(HEADERS)
        if cookies:
            self.session.cookies.update(cookies)

    def _get_sid_and_nonce(self) -> Tuple[str, str]:
        try:
            response: requests.Response = self.session.get(f"{self.base_url}/app")
            response.raise_for_status()
        except RequestException as e:
            raise ConnectionError(
                f"Failed to connect to {self.base_url}: {str(e)}"
            ) from e

        sid: str = self._search_regex(response.text, r'"FdrFJe":"([\d-]+)"', "SID")
        nonce: str = self._search_regex(response.text, r'"SNlM0e":"(.*?)"', "nonce")

        return sid, nonce

    @staticmethod
    def _search_regex(text: str, pattern: str, term: str) -> str:
        match: Optional[re.Match] = re.search(pattern, text)
        if not match:
            raise ValueError(f"Failed to extract {term}.")
        return match.group(1)

    @staticmethod
    def _get_reqid() -> int:
        return int("".join(random.choices(string.digits, k=7)))

    def _construct_params(self, sid: str) -> str:
        return urllib.parse.urlencode(
            {
                "bl": BOT_SERVER,
                "hl": "en",
                "_reqid": self._get_reqid(),
                "rt": "c",
                "f.sid": sid,
            }
        )

    def _construct_payload(self, prompt: str, nonce: str) -> str:
        return urllib.parse.urlencode(
            {
                "at": nonce,
                "f.req": json.dumps([None, json.dumps([[prompt], None, None])]),
            }
        )

    def send_request(self, prompt: str) -> Tuple[str, Optional[int]]:
        try:
            sid, nonce = self._get_sid_and_nonce()
        except ConnectionError as e:
            return str(e), None

        params: str = self._construct_params(sid)
        data: str = self._construct_payload(prompt, nonce)

        try:
            response: requests.Response = self.session.post(
                POST_ENDPOINT,
                params=params,
                data=data,
            )
            response.raise_for_status()
        except RequestException as e:
            return f"Request failed: {str(e)}", None

        return response.text, response.status_code
