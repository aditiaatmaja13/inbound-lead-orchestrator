from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class Lead(BaseModel):
    """
    Core lead object for the inbound lead workflow.

    Input fields:
    - name
    - email
    - company
    - property_address
    - city
    - state
    - country

    Enrichment/output fields are optional and will be filled later
    by the pipeline.
    """

    # Raw input fields
    name: str = Field(..., min_length=1, description="Lead contact full name")
    email: EmailStr = Field(..., description="Lead contact email")
    company: str = Field(..., min_length=1, description="Company name")
    property_address: str = Field(..., min_length=1, description="Property address")
    city: str = Field(..., min_length=1, description="Property city")
    state: str = Field(..., min_length=1, description="Property state")
    country: str = Field(..., min_length=1, description="Property country")

    # Enrichment fields
    company_summary: Optional[str] = None
    company_wikipedia_url: Optional[str] = None
    company_match_quality: Optional[str] = None
    market_population: Optional[int] = None
    median_household_income: Optional[float] = None

    # Scoring/output fields
    lead_score: Optional[int] = None
    lead_priority: Optional[str] = None
    enrichment_confidence: Optional[str] = None
    recommended_action: Optional[str] = None
    score_reasons: List[str] = Field(default_factory=list)
    sales_insights: List[str] = Field(default_factory=list)
    outreach_email: Optional[str] = None

    def full_location(self) -> str:
        """
        Return a human-readable location string.
        """
        return f"{self.city}, {self.state}, {self.country}"

    def has_complete_core_fields(self) -> bool:
        """
        Basic completeness check for the required inbound lead fields.
        """
        required_values = [
            self.name,
            self.email,
            self.company,
            self.property_address,
            self.city,
            self.state,
            self.country,
        ]
        return all(bool(value) for value in required_values)

    def top_reason(self) -> str:
        """
        Return the most decision-useful reason for quick scanning.
        """
        if not self.score_reasons:
            return ""

        deprioritized_prefixes = [
            "Lead includes a contact name",
            "Lead includes a valid contact email",
            "Lead includes a company name",
        ]

        for reason in self.score_reasons:
            if not any(reason.startswith(prefix) for prefix in deprioritized_prefixes):
                return reason

        return self.score_reasons[0]

    def to_output_dict(self) -> dict:
        """
        Return a flattened dict suitable for CSV or JSON output.
        """
        return {
            "name": self.name,
            "email": self.email,
            "company": self.company,
            "property_address": self.property_address,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "company_summary": self.company_summary,
            "company_wikipedia_url": self.company_wikipedia_url,
            "company_match_quality": self.company_match_quality,
            "market_population": self.market_population,
            "median_household_income": self.median_household_income,
            "lead_score": self.lead_score,
            "lead_priority": self.lead_priority,
            "enrichment_confidence": self.enrichment_confidence,
            "recommended_action": self.recommended_action,
            "score_reasons": " | ".join(self.score_reasons),
            "top_reason": self.top_reason(),
            "sales_insights": " | ".join(self.sales_insights),
            "outreach_email": self.outreach_email,
        }