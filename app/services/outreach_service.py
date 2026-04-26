from app.models.lead import Lead
from app.utils.llm_client import generate_email_with_ai


class OutreachService:
    """
    Generates enriched outreach emails using:
    - deterministic API enrichment
    - optional AI generation
    - safe fallback templates
    """

    def generate_outreach_email(self, lead: Lead) -> None:
        company_signal = self._extract_company_signal(lead)
        market_signal = self._build_market_signal(lead)
        personalization_guardrail = self._build_personalization_guardrail(lead)

        context = f"""
Lead:
- First name: {self._first_name(lead)}
- Full name: {lead.name}
- Company: {lead.company}
- Property location: {lead.property_address}, {lead.city}, {lead.state}

Company enrichment from public API:
- Company summary: {lead.company_summary}
- Company match quality: {lead.company_match_quality}
- Company signal: {company_signal}

Market enrichment from Census API:
- Market population: {lead.market_population}
- Median household income: {lead.median_household_income}
- Market signal: {market_signal}

Scoring output:
- Lead score: {lead.lead_score}
- Lead priority: {lead.lead_priority}
- Enrichment confidence: {lead.enrichment_confidence}
- Recommended action: {lead.recommended_action}
- Top reason: {lead.top_reason() if hasattr(lead, "top_reason") else ""}
- Sales insights: {lead.sales_insights}

Personalization rule:
{personalization_guardrail}
"""

        prompt = f"""
Write a polished, natural B2B outbound email for a sales rep.

You are reaching out TO the lead/company. You do not work for their company.

Use the enriched data meaningfully:
- Use the company summary to identify what the company does, but only if company match quality is High.
- Use the market signal to explain why response speed, inbound handling, or operational consistency matters.
- Use the lead priority/recommended action to decide urgency.
- Do NOT dump raw statistics. Convert them into business implications.
- If company match quality is Low, do NOT mention the company summary. Use only location/property context.

Requirements:
- Include a subject line.
- Use the lead's first name: {self._first_name(lead)}
- 90–130 words.
- Conversational and specific.
- Sound like a real SDR, not a marketing brochure.
- No placeholders like [Name], [Company], [Your Company].
- Avoid generic phrases: "I hope this finds you well", "explore opportunities", "enhance your efforts", "vibrant market", "synergies".
- Mention EliseAI by name once as the solution provider.
- End with a clear, casual CTA for a 15-minute chat.

Preferred structure:
1. Subject line
2. Personalized reason for reaching out
3. Business challenge inferred from enrichment
4. EliseAI value proposition
5. Short CTA

Context:
{context}

Return only the email.
"""

        try:
            email = generate_email_with_ai(prompt)
            lead.outreach_email = self._clean_ai_email(email)

        except Exception as e:
            print(f"[AI] Falling back to template due to error: {e}")
            lead.outreach_email = self._build_fallback_email(
                lead=lead,
                company_signal=company_signal,
                market_signal=market_signal,
            )

    # ---------- fallback email ----------

    def _build_fallback_email(
        self,
        lead: Lead,
        company_signal: str | None,
        market_signal: str | None,
    ) -> str:
        subject = self._build_subject_line(lead)
        first_name = self._first_name(lead)

        intro = self._build_personalized_intro(
            lead=lead,
            company_signal=company_signal,
            market_signal=market_signal,
        )

        value = self._build_value_line(
            lead=lead,
            company_signal=company_signal,
            market_signal=market_signal,
        )

        return (
            f"{subject}\n\n"
            f"Hi {first_name},\n\n"
            f"{intro}\n\n"
            f"{value}\n\n"
            "Would you be open to a quick 15-minute chat next week?\n\n"
            "Best,\n[Your Name]"
        )

    def _build_subject_line(self, lead: Lead) -> str:
        if lead.lead_priority == "High" and lead.city:
            return f"Subject: Inbound response speed in {lead.city}"
        if lead.company:
            return f"Subject: Quick thought for {lead.company}"
        return "Subject: Quick thought"

    def _build_personalized_intro(
        self,
        lead: Lead,
        company_signal: str | None,
        market_signal: str | None,
    ) -> str:
        if lead.company_match_quality == "High" and company_signal and market_signal:
            return (
                f"I came across {lead.company} and noticed the company is focused on {company_signal}. "
                f"Given {market_signal}, I figured it might be worth reaching out."
            )

        if lead.company_match_quality == "High" and company_signal:
            return (
                f"I came across {lead.company} and noticed the company is focused on {company_signal}. "
                f"That made me think inbound responsiveness and operational consistency may be relevant for your team."
            )

        if market_signal:
            return (
                f"I saw that you manage property in {lead.city}, {lead.state}. "
                f"Given {market_signal}, I figured it might be worth reaching out."
            )

        return (
            f"I saw that you manage property in {lead.city}, {lead.state}, "
            f"and figured it might be worth reaching out."
        )

    def _build_value_line(
        self,
        lead: Lead,
        company_signal: str | None,
        market_signal: str | None,
    ) -> str:
        if lead.lead_priority == "High":
            return (
                "For teams handling leasing or resident-facing inquiries, even small delays can mean missed demand. "
                "EliseAI helps automate follow-up, improve response speed, and reduce the manual work that slows teams down."
            )

        if lead.lead_priority == "Medium":
            return (
                "EliseAI helps property teams handle inbound inquiries more consistently, reduce manual follow-up, "
                "and give reps more time to focus on qualified opportunities."
            )

        return (
            "EliseAI helps teams create a more consistent inbound follow-up process without adding more manual work."
        )

    # ---------- enrichment interpretation helpers ----------

    def _extract_company_signal(self, lead: Lead) -> str | None:
        """
        Converts Wikipedia/company enrichment into a usable business signal.
        Only use it when the company match is reliable enough.
        """
        if lead.company_match_quality != "High" or not lead.company_summary:
            return None

        summary = lead.company_summary.lower()

        if "real estate investment trust" in summary or "reit" in summary:
            return "apartment communities and real estate investment operations"

        if "commercial real estate" in summary:
            return "commercial real estate services and property operations"

        if "property management" in summary:
            return "property management and resident-facing operations"

        if "real estate" in summary:
            return "real estate operations"

        if "apartments" in summary or "multifamily" in summary:
            return "apartment communities and leasing operations"

        if "leasing" in summary:
            return "leasing workflows and property operations"

        if "investment management" in summary:
            return "real estate investment and client-facing operations"

        return None

    def _build_market_signal(self, lead: Lead) -> str | None:
        """
        Converts Census enrichment into a readable business implication.
        """
        if not lead.market_population:
            return None

        if lead.market_population >= 5_000_000:
            return (
                f"{lead.city} is an extremely large market where inbound demand can move quickly"
            )

        if lead.market_population >= 1_000_000:
            return (
                f"{lead.city} is a large market where response speed and coverage can matter a lot"
            )

        if lead.market_population >= 250_000:
            return (
                f"{lead.city} is a mid-sized market where consistent follow-up can help teams capture more qualified demand"
            )

        return (
            f"{lead.city} is a smaller market where every qualified inbound inquiry can matter more"
        )

    def _build_personalization_guardrail(self, lead: Lead) -> str:
        if lead.company_match_quality == "High":
            return (
                "Company match is high. It is safe to reference the company summary, but do so naturally."
            )

        if lead.company_match_quality == "Medium":
            return (
                "Company match is medium. Reference the company name and market, but avoid relying heavily on the company summary."
            )

        return (
            "Company match is low. Do not use the company summary. Personalize using city, property location, and market context only."
        )

    # ---------- utility helpers ----------

    @staticmethod
    def _first_name(lead: Lead) -> str:
        if not lead.name:
            return "there"
        return lead.name.strip().split()[0]

    @staticmethod
    def _clean_ai_email(email: str) -> str:
        """
        Basic cleanup in case the LLM adds extra whitespace.
        """
        cleaned = email.strip()
        cleaned = cleaned.replace("[Your Company]", "EliseAI")
        cleaned = cleaned.replace("[Company]", "")
        cleaned = cleaned.replace("[Name]", "")
        return cleaned