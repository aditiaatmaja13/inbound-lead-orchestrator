from typing import Dict, Optional
import requests
from app.utils.http import get_json


class CensusClient:
    """
    Small client for fetching basic market-level enrichment
    from the U.S. Census API.

    MVP fields:
    - total population
    - median household income

    We query ACS 5-year profile data at the 'place' level.
    """

    BASE_URL = "https://api.census.gov/data/2022/acs/acs5/profile"
    STATE_SEARCH_URL = "https://api.census.gov/data/2020/dec/pl"

    def __init__(self, timeout: int = 20):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "inbound-lead-orchestrator/1.0"
        }

    def get_city_market_data(self, city: str, state: str) -> Dict[str, Optional[float]]:
        """
        Main helper:
        1. Resolve state FIPS code from state name/abbreviation
        2. Find matching place row for city
        3. Return population + median household income

        Returns:
        {
            "market_population": int | None,
            "median_household_income": float | None
        }
        """
        try:
            state_code = self._resolve_state_code(state)
            if not state_code:
                return self._empty_response()

            place_match = self._find_place(city=city, state_code=state_code)
            if not place_match:
                return self._empty_response()

            place_code = place_match["place_code"]

            data = self._fetch_profile_data(
                state_code=state_code,
                place_code=place_code,
            )

            return {
                "market_population": self._safe_int(data.get("population")),
                "median_household_income": self._safe_float(data.get("median_household_income")),
            }

        except requests.RequestException as exc:
            print(f"[CensusClient] Request failed for {city}, {state}: {exc}")
            return self._empty_response()

    def _resolve_state_code(self, state: str) -> Optional[str]:
        """
        Resolve a state name or 2-letter abbreviation to Census state FIPS code.
        """
        state_map = {
            "AL": "01", "ALABAMA": "01",
            "AK": "02", "ALASKA": "02",
            "AZ": "04", "ARIZONA": "04",
            "AR": "05", "ARKANSAS": "05",
            "CA": "06", "CALIFORNIA": "06",
            "CO": "08", "COLORADO": "08",
            "CT": "09", "CONNECTICUT": "09",
            "DE": "10", "DELAWARE": "10",
            "DC": "11", "DISTRICT OF COLUMBIA": "11",
            "FL": "12", "FLORIDA": "12",
            "GA": "13", "GEORGIA": "13",
            "HI": "15", "HAWAII": "15",
            "ID": "16", "IDAHO": "16",
            "IL": "17", "ILLINOIS": "17",
            "IN": "18", "INDIANA": "18",
            "IA": "19", "IOWA": "19",
            "KS": "20", "KANSAS": "20",
            "KY": "21", "KENTUCKY": "21",
            "LA": "22", "LOUISIANA": "22",
            "ME": "23", "MAINE": "23",
            "MD": "24", "MARYLAND": "24",
            "MA": "25", "MASSACHUSETTS": "25",
            "MI": "26", "MICHIGAN": "26",
            "MN": "27", "MINNESOTA": "27",
            "MS": "28", "MISSISSIPPI": "28",
            "MO": "29", "MISSOURI": "29",
            "MT": "30", "MONTANA": "30",
            "NE": "31", "NEBRASKA": "31",
            "NV": "32", "NEVADA": "32",
            "NH": "33", "NEW HAMPSHIRE": "33",
            "NJ": "34", "NEW JERSEY": "34",
            "NM": "35", "NEW MEXICO": "35",
            "NY": "36", "NEW YORK": "36",
            "NC": "37", "NORTH CAROLINA": "37",
            "ND": "38", "NORTH DAKOTA": "38",
            "OH": "39", "OHIO": "39",
            "OK": "40", "OKLAHOMA": "40",
            "OR": "41", "OREGON": "41",
            "PA": "42", "PENNSYLVANIA": "42",
            "RI": "44", "RHODE ISLAND": "44",
            "SC": "45", "SOUTH CAROLINA": "45",
            "SD": "46", "SOUTH DAKOTA": "46",
            "TN": "47", "TENNESSEE": "47",
            "TX": "48", "TEXAS": "48",
            "UT": "49", "UTAH": "49",
            "VT": "50", "VERMONT": "50",
            "VA": "51", "VIRGINIA": "51",
            "WA": "53", "WASHINGTON": "53",
            "WV": "54", "WEST VIRGINIA": "54",
            "WI": "55", "WISCONSIN": "55",
            "WY": "56", "WYOMING": "56",
        }

        return state_map.get(state.strip().upper())

    def _find_place(self, city: str, state_code: str) -> Optional[Dict[str, str]]:
        """
        Find the best matching place code for a city within a state.

        Uses 2020 decennial place list and filters in Python.
        """
        params = {
            "get": "NAME",
            "for": "place:*",
            "in": f"state:{state_code}",
        }

        rows = get_json(
            self.STATE_SEARCH_URL,
            params=params,
            headers=self.headers,
            timeout=self.timeout,
        )
        if len(rows) < 2:
            return None

        header = rows[0]
        data_rows = rows[1:]

        name_idx = header.index("NAME")
        place_idx = header.index("place")

        city_normalized = city.strip().lower()

        exact_matches = []
        startswith_matches = []

        for row in data_rows:
            place_name = row[name_idx]
            place_code = row[place_idx]

            place_name_normalized = place_name.lower()

            # Example NAME values:
            # "New York city, New York"
            # "Albany city, New York"
            if place_name_normalized.startswith(city_normalized):
                startswith_matches.append({
                    "place_name": place_name,
                    "place_code": place_code,
                })

            if place_name_normalized == f"{city_normalized} city, {self._state_name_from_code(state_code).lower()}":
                exact_matches.append({
                    "place_name": place_name,
                    "place_code": place_code,
                })

        if exact_matches:
            return exact_matches[0]

        if startswith_matches:
            return startswith_matches[0]

        return None

    def _fetch_profile_data(self, state_code: str, place_code: str) -> Dict[str, Optional[str]]:
        """
        Fetch ACS profile fields for the matched place.

        Variables:
        - DP05_0001E = total population
        - DP03_0062E = median household income (dollars)
        """
        params = {
            "get": "DP05_0001E,DP03_0062E",
            "for": f"place:{place_code}",
            "in": f"state:{state_code}",
        }

        rows = get_json(
            self.BASE_URL,
            params=params,
            headers=self.headers,
            timeout=self.timeout,
        )
        if len(rows) < 2:
            return {
                "population": None,
                "median_household_income": None,
            }

        header = rows[0]
        values = rows[1]

        row_dict = dict(zip(header, values))

        return {
            "population": row_dict.get("DP05_0001E"),
            "median_household_income": row_dict.get("DP03_0062E"),
        }

    def _state_name_from_code(self, state_code: str) -> str:
        reverse_map = {
            "01": "Alabama",
            "02": "Alaska",
            "04": "Arizona",
            "05": "Arkansas",
            "06": "California",
            "08": "Colorado",
            "09": "Connecticut",
            "10": "Delaware",
            "11": "District of Columbia",
            "12": "Florida",
            "13": "Georgia",
            "15": "Hawaii",
            "16": "Idaho",
            "17": "Illinois",
            "18": "Indiana",
            "19": "Iowa",
            "20": "Kansas",
            "21": "Kentucky",
            "22": "Louisiana",
            "23": "Maine",
            "24": "Maryland",
            "25": "Massachusetts",
            "26": "Michigan",
            "27": "Minnesota",
            "28": "Mississippi",
            "29": "Missouri",
            "30": "Montana",
            "31": "Nebraska",
            "32": "Nevada",
            "33": "New Hampshire",
            "34": "New Jersey",
            "35": "New Mexico",
            "36": "New York",
            "37": "North Carolina",
            "38": "North Dakota",
            "39": "Ohio",
            "40": "Oklahoma",
            "41": "Oregon",
            "42": "Pennsylvania",
            "44": "Rhode Island",
            "45": "South Carolina",
            "46": "South Dakota",
            "47": "Tennessee",
            "48": "Texas",
            "49": "Utah",
            "50": "Vermont",
            "51": "Virginia",
            "53": "Washington",
            "54": "West Virginia",
            "55": "Wisconsin",
            "56": "Wyoming",
        }
        return reverse_map.get(state_code, "")

    @staticmethod
    def _safe_int(value: Optional[str]) -> Optional[int]:
        if value is None or value in ("", "null", "-666666666"):
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_float(value: Optional[str]) -> Optional[float]:
        if value is None or value in ("", "null", "-666666666"):
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _empty_response() -> Dict[str, Optional[float]]:
        return {
            "market_population": None,
            "median_household_income": None,
        }