from typing import Dict, Optional
from urllib.parse import quote

from app.utils.http import get_json


class WikipediaClient:
    """

    Strategy:
    1. Search Wikipedia by company name
    2. Fetch summary for best result
    3. Fallback: try direct summary lookup using company name
    4. Fail gracefully if Wikipedia has no usable result
    """

    BASE_URL = "https://en.wikipedia.org/w/api.php"
    SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "inbound-lead-orchestrator/1.0 (demo project; contact: example@example.com)"
        }

    def search_company(self, company_name: str) -> Optional[str]:
        """
        Search Wikipedia and return the top matching page title.
        """
        params = {
            "action": "query",
            "list": "search",
            "srsearch": company_name,
            "format": "json",
        }

        data = get_json(self.BASE_URL, params=params, headers=self.headers)
        results = data.get("query", {}).get("search", [])

        if not results:
            return None

        return results[0].get("title")

    def get_page_summary(self, page_title: str) -> Dict[str, Optional[str]]:
        """
        Fetch summary for a specific page title.
        """
        safe_title = quote(page_title, safe="")
        url = f"{self.SUMMARY_URL}/{safe_title}"

        data = get_json(url, headers=self.headers)

        return {
            "title": data.get("title"),
            "summary": data.get("extract"),
            "url": data.get("content_urls", {}).get("desktop", {}).get("page"),
        }

    def get_company_context(self, company_name: str) -> Dict[str, Optional[str]]:
        """
        Search first, then fallback to direct summary lookup.
        """
        try:
            page_title = self.search_company(company_name)

            if page_title:
                summary_data = self.get_page_summary(page_title)
                if summary_data.get("summary"):
                    return summary_data

        except Exception as exc:
            print(f"[WikipediaClient] Search path failed for '{company_name}': {exc}")

        try:
            fallback_data = self.get_page_summary(company_name)
            if fallback_data.get("summary"):
                return fallback_data

        except Exception as exc:
            print(f"[WikipediaClient] Direct summary fallback failed for '{company_name}': {exc}")

        return {
            "title": None,
            "summary": None,
            "url": None,
        }