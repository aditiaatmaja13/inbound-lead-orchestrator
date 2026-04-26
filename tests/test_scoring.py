from app.models.lead import Lead
from app.services.scoring_service import ScoringService


def test_high_quality_real_estate_lead_scores_high():
    lead = Lead(
        name="Jane Smith",
        email="jane@example.com",
        company="CBRE",
        property_address="200 Park Ave",
        city="New York",
        state="NY",
        country="USA",
        company_summary="CBRE is a commercial real estate services and investment firm.",
        company_wikipedia_url="https://en.wikipedia.org/wiki/CBRE_Group",
        company_match_quality="High",
        market_population=8622467,
        median_household_income=76607,
    )

    scored = ScoringService().score_lead(lead)

    assert scored.lead_score >= 80
    assert scored.lead_priority == "High"
    assert scored.enrichment_confidence == "High"
    assert scored.recommended_action == "Send outreach now"