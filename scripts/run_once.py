from app.services.pipeline_service import PipelineService


def main() -> None:
    input_csv_path = "scripts/sample_input.csv"
    output_csv_path = "data/output/enriched_leads.csv"

    pipeline_service = PipelineService()
    processed_leads = pipeline_service.process_csv(
        input_csv_path=input_csv_path,
        output_csv_path=output_csv_path,
    )

    print("\n=== PROCESSING SUMMARY ===")
    print(f"Processed leads: {len(processed_leads)}")

    for lead in processed_leads:
        print("\n" + "=" * 40)
        print(f"Company: {lead.company}")
        print(f"Location: {lead.city}, {lead.state}")
        print(f"Score: {lead.lead_score}")
        print(f"Priority: {lead.lead_priority}")
        print(f"Enrichment confidence: {lead.enrichment_confidence}")
        print(f"Recommended action: {lead.recommended_action}")

        print("\nTop reasons:")
        for reason in lead.score_reasons[:3]:
            print(f"- {reason}")

        print("\nTop insights:")
        for insight in lead.sales_insights[:3]:
            print(f"- {insight}")


if __name__ == "__main__":
    main()