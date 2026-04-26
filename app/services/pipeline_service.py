import csv
import os
from typing import List

from pydantic import ValidationError

from app.models.lead import Lead
from app.services.enrichment_service import EnrichmentService
from app.services.outreach_service import OutreachService
from app.services.scoring_service import ScoringService


class PipelineService:
    """
    Main orchestration service for the inbound lead workflow.

    Responsibilities:
    - load lead rows from CSV
    - validate each row
    - enrich each lead
    - score each lead
    - generate outreach
    - write enriched results to CSV
    """

    def __init__(
        self,
        enrichment_service: EnrichmentService | None = None,
        scoring_service: ScoringService | None = None,
        outreach_service: OutreachService | None = None,
    ):
        self.enrichment_service = enrichment_service or EnrichmentService()
        self.scoring_service = scoring_service or ScoringService()
        self.outreach_service = outreach_service or OutreachService()

    def process_csv(self, input_csv_path: str, output_csv_path: str) -> List[Lead]:
        """
        Read input leads from CSV, process them, and write output CSV.
        """
        raw_rows = self._read_csv(input_csv_path)
        processed_leads: List[Lead] = []

        for index, row in enumerate(raw_rows, start=1):
            print(f"[Pipeline] Processing row {index}: {row.get('company')}")
            try:
                lead = Lead(**row)

                lead = self.enrichment_service.enrich_lead(lead)
                lead = self.scoring_service.score_lead(lead)
                self.outreach_service.generate_outreach_email(lead)

                processed_leads.append(lead)

            except ValidationError as exc:
                print(f"[PipelineService] Skipping invalid row {index}: {exc}")

        self._write_output_csv(processed_leads, output_csv_path)
        return processed_leads

    def _read_csv(self, file_path: str) -> List[dict]:
        """
        Read rows from an input CSV.
        """
        with open(file_path, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            return list(reader)

    def _write_output_csv(self, leads: List[Lead], file_path: str) -> None:
        """
        Write processed lead output to CSV.
        """
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        if not leads:
            print("[PipelineService] No valid leads to write.")
            return

        output_rows = [lead.to_output_dict() for lead in leads]
        fieldnames = list(output_rows[0].keys())

        with open(file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(output_rows)

        print(f"[PipelineService] Wrote {len(leads)} leads to {file_path}")