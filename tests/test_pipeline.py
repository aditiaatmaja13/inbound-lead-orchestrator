import csv

from app.services.pipeline_service import PipelineService


class FakeEnrichmentService:
    def enrich_lead(self, lead):
        lead.company_summary = "CBRE is a commercial real estate services firm."
        lead.company_wikipedia_url = "https://en.wikipedia.org/wiki/CBRE_Group"
        lead.company_match_quality = "High"
        lead.market_population = 8622467
        lead.median_household_income = 76607
        return lead


class FakeOutreachService:
    def generate_outreach_email(self, lead):
        lead.outreach_email = "Subject: Test\n\nHi Jane,\n\nTest email."


def test_pipeline_processes_csv(tmp_path):
    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "output.csv"

    with open(input_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "name",
                "email",
                "company",
                "property_address",
                "city",
                "state",
                "country",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "name": "Jane Smith",
                "email": "jane@example.com",
                "company": "CBRE",
                "property_address": "200 Park Ave",
                "city": "New York",
                "state": "NY",
                "country": "USA",
            }
        )

    pipeline = PipelineService(
        enrichment_service=FakeEnrichmentService(),
        outreach_service=FakeOutreachService(),
    )

    processed = pipeline.process_csv(
        input_csv_path=str(input_path),
        output_csv_path=str(output_path),
    )

    assert len(processed) == 1
    assert processed[0].lead_priority == "High"
    assert output_path.exists()