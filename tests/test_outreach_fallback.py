import os

from app.models.lead import Lead
from app.services.outreach_service import OutreachService


def test_outreach_falls_back_without_openai_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    lead = Lead(
        name="Jane Smith",
        email="jane@example.com",
        company="CBRE",
        property_address="200 Park Ave",
        city="New York",
        state="NY",
        country="USA",
        company_summary="CBRE is a commercial real estate services firm.",
        company_wikipedia_url="https://en.wikipedia.org/wiki/CBRE_Group",
        company_match_quality="High",
        market_population=8622467,
        median_household_income=76607,
        lead_score=95,
        lead_priority="High",
        enrichment_confidence="High",
        recommended_action="Send outreach now",
    )

    OutreachService().generate_outreach_email(lead)

    assert lead.outreach_email is not None
    assert "Subject:" in lead.outreach_email
    assert "Hi Jane" in lead.outreach_email
    assert "EliseAI" in lead.outreach_email