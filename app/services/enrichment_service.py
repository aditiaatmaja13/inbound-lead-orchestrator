from app.api_clients.census_client import CensusClient
from app.api_clients.wikipedia_client import WikipediaClient
from app.models.lead import Lead


class EnrichmentService:
    """
    Enriches a lead using public data sources.

    Current sources:
    - Wikipedia for company context
    - Census for market signals
    """

    def __init__(
        self,
        wikipedia_client: WikipediaClient | None = None,
        census_client: CensusClient | None = None,
    ):
        self.wikipedia_client = wikipedia_client or WikipediaClient()
        self.census_client = census_client or CensusClient()

    def enrich_lead(self, lead: Lead) -> Lead:
        """
        Enrich a lead in place and return it.
        """
        self._enrich_company_context(lead)
        self._enrich_market_context(lead)
        return lead

    def _enrich_company_context(self, lead: Lead) -> None:
        """
        Use Wikipedia to get company summary + URL, then estimate
        whether the matched page looks like the intended company.
        """
        if not lead.company or not lead.company.strip():
            lead.company_match_quality = "Low"
            return

        context = self.wikipedia_client.get_company_context(lead.company)

        lead.company_summary = context.get("summary")
        lead.company_wikipedia_url = context.get("url")
        lead.company_match_quality = self._estimate_company_match_quality(
            input_company=lead.company,
            matched_title=context.get("title"),
            summary=context.get("summary"),
        )

    def _enrich_market_context(self, lead: Lead) -> None:
        """
        Use Census to get population + income at the city/place level.
        """
        if not lead.city or not lead.state:
            return

        market_data = self.census_client.get_city_market_data(
            city=lead.city,
            state=lead.state,
        )

        lead.market_population = market_data.get("market_population")
        lead.median_household_income = market_data.get("median_household_income")

    @staticmethod
    def _estimate_company_match_quality(
        input_company: str,
        matched_title: str | None,
        summary: str | None,
    ) -> str:
        """
        Estimate whether the public company context likely matches the input company.

        This is not perfect entity resolution, but it is useful for MVP confidence scoring.
        """
        if not matched_title and not summary:
            return "Low"

        input_normalized = input_company.lower().replace("&", "and").strip()
        title_normalized = (matched_title or "").lower().replace("&", "and").strip()
        summary_normalized = (summary or "").lower().replace("&", "and").strip()

        input_tokens = {
            token
            for token in input_normalized.replace(",", "").replace(".", "").split()
            if len(token) > 2
        }

        if not input_tokens:
            return "Low"

        title_token_hits = sum(1 for token in input_tokens if token in title_normalized)
        summary_token_hits = sum(1 for token in input_tokens if token in summary_normalized)

        title_match_ratio = title_token_hits / len(input_tokens)
        summary_match_ratio = summary_token_hits / len(input_tokens)

        if title_match_ratio >= 0.75:
            return "High"

        if title_match_ratio >= 0.4 or summary_match_ratio >= 0.6:
            return "Medium"

        return "Low"