from typing import Dict, List, Tuple

from app.models.lead import Lead


class ScoringService:
    """
    Lead scoring service for the MVP.

    This is an SDR prioritization score, not a conversion prediction score.

    Dimensions:
    - Data completeness
    - Market attractiveness
    - Company relevance
    - Enrichment confidence
    """

    def score_lead(self, lead: Lead) -> Lead:
        score = 0
        reasons: List[str] = []
        insights: List[str] = []

        completeness_score, completeness_reasons = self._score_data_completeness(lead)
        score += completeness_score
        reasons.extend(completeness_reasons)

        market_score, market_reasons, market_insights = self._score_market_attractiveness(lead)
        score += market_score
        reasons.extend(market_reasons)
        insights.extend(market_insights)

        company_score, company_reasons, company_insights = self._score_company_context(lead)
        score += company_score
        reasons.extend(company_reasons)
        insights.extend(company_insights)

        confidence_score, confidence_reasons, confidence_insights = self._score_enrichment_confidence(lead)
        score += confidence_score
        reasons.extend(confidence_reasons)
        insights.extend(confidence_insights)

        score = max(0, min(score, 100))
        priority = self._map_score_to_priority(score)
        confidence = self._map_enrichment_confidence(lead)

        reasons = self._prioritize_reasons(reasons)
        insights = self._prioritize_insights(insights)

        lead.lead_score = score
        lead.lead_priority = priority
        lead.score_reasons = reasons
        lead.sales_insights = insights
        lead.enrichment_confidence = confidence
        lead.recommended_action = self._recommended_action(priority, confidence)

        return lead

    def _score_data_completeness(self, lead: Lead) -> Tuple[int, List[str]]:
        score = 0
        reasons: List[str] = []

        if lead.name:
            score += 4
            reasons.append("Lead includes a contact name.")
        if lead.email:
            score += 4
            reasons.append("Lead includes a valid contact email.")
        if lead.company:
            score += 4
            reasons.append("Lead includes a company name.")
        if lead.property_address:
            score += 6
            reasons.append("Lead includes a property address.")
        if lead.city and lead.state and lead.country:
            score += 7
            reasons.append("Lead includes complete location details.")

        return score, reasons

    def _score_market_attractiveness(self, lead: Lead) -> Tuple[int, List[str], List[str]]:
        score = 0
        reasons: List[str] = []
        insights: List[str] = []

        if lead.market_population is not None:
            if lead.market_population >= 5_000_000:
                score += 18
                reasons.append("Lead is in a very large market with population above 5M.")
                insights.append(f"{lead.city} appears to be a very large market by population.")
            elif lead.market_population >= 1_000_000:
                score += 14
                reasons.append("Lead is in a large market with population above 1M.")
                insights.append(f"{lead.city} appears to be a large market by population.")
            elif lead.market_population >= 250_000:
                score += 9
                reasons.append("Lead is in a mid-sized market with population above 250K.")
                insights.append(f"{lead.city} appears to be a mid-sized market.")
            else:
                score += 4
                reasons.append("Lead is in a smaller market.")
                insights.append(f"{lead.city} appears to be a smaller market.")

        if lead.median_household_income is not None:
            if lead.median_household_income >= 120_000:
                score += 12
                reasons.append("Median household income is very strong in this market.")
                insights.append("Local income levels suggest a very strong market.")
            elif lead.median_household_income >= 90_000:
                score += 9
                reasons.append("Median household income is strong in this market.")
                insights.append("Local income levels suggest a strong market.")
            elif lead.median_household_income >= 70_000:
                score += 6
                reasons.append("Median household income is moderate-to-strong in this market.")
                insights.append("Local income levels suggest a moderately attractive market.")
            elif lead.median_household_income >= 50_000:
                score += 3
                reasons.append("Median household income is moderate in this market.")
                insights.append("Local income levels suggest a workable but less premium market.")
            else:
                score += 1
                reasons.append("Median household income is modest in this market.")
                insights.append("Local income levels suggest a lower-priority market.")

        return score, reasons, insights

    def _score_company_context(self, lead: Lead) -> Tuple[int, List[str], List[str]]:
        score = 0
        reasons: List[str] = []
        insights: List[str] = []

        if lead.company_summary:
            summary_length = len(lead.company_summary)

            if summary_length >= 250:
                score += 16
                reasons.append("Strong company context was found for personalization.")
                insights.append("Company research is rich enough to support tailored outreach.")
            elif summary_length >= 120:
                score += 12
                reasons.append("Useful company context was found for personalization.")
                insights.append("Some company-specific personalization is possible.")
            else:
                score += 6
                reasons.append("Limited company context was found.")
                insights.append("Only light company personalization is possible.")
        else:
            reasons.append("No strong public company summary was found.")
            insights.append("Rep may need to validate the company manually before outreach.")

        if lead.company_wikipedia_url:
            score += 6
            reasons.append("Public company reference URL is available for rep validation.")
            insights.append("Rep can quickly validate company context before outreach.")

        company_name_lower = lead.company.lower().strip() if lead.company else ""
        if company_name_lower:
            real_estate_keywords = [
                "realty",
                "properties",
                "property",
                "commercial real estate",
                "real estate",
                "management",
                "leasing",
                "housing",
                "apartments",
            ]
            summary_lower = (lead.company_summary or "").lower()

            if any(keyword in company_name_lower for keyword in real_estate_keywords) or any(
                keyword in summary_lower for keyword in real_estate_keywords
            ):
                score += 8
                reasons.append("Company appears relevant to real estate or property operations.")
                insights.append("This looks more aligned with the target customer profile.")

        if lead.company_match_quality == "High":
            score += 6
            reasons.append("Company match quality is high.")
            insights.append("Public company enrichment appears to match the input company well.")
        elif lead.company_match_quality == "Medium":
            score += 3
            reasons.append("Company match quality is moderate.")
            insights.append("Rep should quickly verify the public company context before using it.")
        elif lead.company_match_quality == "Low":
            score -= 8
            reasons.append("Company match quality is low.")
            insights.append("Public company enrichment may not match the intended lead.")

        return score, reasons, insights

    def _score_enrichment_confidence(self, lead: Lead) -> Tuple[int, List[str], List[str]]:
        score = 0
        reasons: List[str] = []
        insights: List[str] = []

        filled_fields = 0
        for value in [
            lead.company_summary,
            lead.company_wikipedia_url,
            lead.market_population,
            lead.median_household_income,
        ]:
            if value is not None:
                filled_fields += 1

        if filled_fields == 4 and lead.company_match_quality == "High":
            score += 15
            reasons.append("All major enrichment fields were successfully populated with a high-quality company match.")
            insights.append("This lead has high enrichment confidence.")
        elif filled_fields >= 3 and lead.company_match_quality in {"High", "Medium"}:
            score += 10
            reasons.append("Most enrichment fields were populated with acceptable company match quality.")
            insights.append("This lead has solid enrichment confidence.")
        elif filled_fields >= 2:
            score += 5
            reasons.append("Some enrichment fields were populated, but match quality may need review.")
            insights.append("This lead has moderate enrichment confidence.")
        else:
            reasons.append("Enrichment coverage is limited.")
            insights.append("This lead may require manual verification before outreach.")

        return score, reasons, insights

    @staticmethod
    def _map_score_to_priority(score: int) -> str:
        if score >= 80:
            return "High"
        if score >= 55:
            return "Medium"
        return "Low"

    @staticmethod
    def _recommended_action(priority: str, confidence: str) -> str:
        if priority == "High" and confidence == "High":
            return "Send outreach now"
        if priority == "High":
            return "Review quickly, then send outreach"
        if priority == "Medium":
            return "Review and prioritize this week"
        return "Hold for manual review or lower-priority follow-up"

    @staticmethod
    def _map_enrichment_confidence(lead: Lead) -> str:
        filled_fields = 0
        for value in [
            lead.company_summary,
            lead.company_wikipedia_url,
            lead.market_population,
            lead.median_household_income,
        ]:
            if value is not None:
                filled_fields += 1

        if filled_fields >= 3 and lead.company_match_quality == "High":
            return "High"

        if filled_fields >= 2 and lead.company_match_quality in {"High", "Medium"}:
            return "Medium"

        return "Low"

    @staticmethod
    def _prioritize_reasons(reasons: List[str]) -> List[str]:
        priority_terms = [
            "very large market",
            "large market",
            "company match quality is high",
            "company match quality is moderate",
            "company match quality is low",
            "strong company context",
            "useful company context",
            "real estate or property operations",
            "all major enrichment fields",
            "most enrichment fields",
            "median household income",
            "public company reference url",
            "property address",
            "complete location details",
            "contact name",
            "valid contact email",
            "company name",
        ]

        def rank(reason: str) -> int:
            lower_reason = reason.lower()
            for index, term in enumerate(priority_terms):
                if term in lower_reason:
                    return index
            return len(priority_terms)

        return sorted(reasons, key=rank)

    @staticmethod
    def _prioritize_insights(insights: List[str]) -> List[str]:
        priority_terms = [
            "target customer profile",
            "very large market",
            "large market",
            "strong market",
            "tailored outreach",
            "high enrichment confidence",
            "solid enrichment confidence",
        ]

        def rank(insight: str) -> int:
            lower_insight = insight.lower()
            for index, term in enumerate(priority_terms):
                if term in lower_insight:
                    return index
            return len(priority_terms)

        return sorted(insights, key=rank)

    def explain_score_breakdown(self, lead: Lead) -> Dict[str, object]:
        return {
            "company": lead.company,
            "location": lead.full_location(),
            "lead_score": lead.lead_score,
            "lead_priority": lead.lead_priority,
            "enrichment_confidence": lead.enrichment_confidence,
            "score_reasons": lead.score_reasons,
            "sales_insights": lead.sales_insights,
        }
    
