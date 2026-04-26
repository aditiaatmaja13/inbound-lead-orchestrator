import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import tempfile

import pandas as pd
import streamlit as st

from app.services.pipeline_service import PipelineService


st.set_page_config(
    page_title="Inbound Lead Orchestrator",
    page_icon="📈",
    layout="wide",
)


def style_priority(value: str) -> str:
    if value == "High":
        return "background-color: #1f8f4d; color: white; font-weight: bold;"
    if value == "Medium":
        return "background-color: #c28a00; color: white; font-weight: bold;"
    if value == "Low":
        return "background-color: #b42318; color: white; font-weight: bold;"
    return ""


def main() -> None:
    st.sidebar.title("Inbound Lead Orchestrator")

    st.sidebar.markdown("### Expected CSV columns")
    st.sidebar.code(
        "name,email,company,property_address,city,state,country",
        language="text",
    )

    st.sidebar.markdown("### What this tool does")
    st.sidebar.write(
        "Enriches inbound leads, scores them, generates sales insights, "
        "and creates draft outreach emails."
    )

    st.title("Inbound Lead Orchestrator")

    st.divider()

    uploaded_file = st.file_uploader(
        "Upload lead CSV",
        type=["csv"],
    )

    if uploaded_file is None:
        st.info("Upload a CSV file to begin.")
        return

    input_df = pd.read_csv(uploaded_file)

    st.markdown("### Input Preview")
    st.dataframe(input_df, use_container_width=True)

    required_columns = {
        "name",
        "email",
        "company",
        "property_address",
        "city",
        "state",
        "country",
    }

    missing_columns = required_columns - set(input_df.columns)

    if missing_columns:
        st.error(f"Missing required columns: {', '.join(sorted(missing_columns))}")
        return

    st.divider()

    if st.button("Process Leads", type="primary"):
        with st.spinner("Enriching and scoring leads..."):
            with tempfile.TemporaryDirectory() as temp_dir:
                input_path = os.path.join(temp_dir, "input.csv")
                output_path = os.path.join(temp_dir, "enriched_leads.csv")

                input_df.to_csv(input_path, index=False)

                pipeline_service = PipelineService()
                processed_leads = pipeline_service.process_csv(
                    input_csv_path=input_path,
                    output_csv_path=output_path,
                )

                output_df = pd.read_csv(output_path)

        st.success(f"Processed {len(processed_leads)} leads.")

        st.divider()

        total_leads = len(output_df)
        high_priority_count = (output_df["lead_priority"] == "High").sum()
        medium_priority_count = (output_df["lead_priority"] == "Medium").sum()
        avg_score = round(output_df["lead_score"].mean(), 1)

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Leads", total_leads)
        col2.metric("High Priority", high_priority_count)
        col3.metric("Medium Priority", medium_priority_count)
        col4.metric("Average Score", avg_score)

        st.divider()

        csv_bytes = output_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download enriched leads CSV",
            data=csv_bytes,
            file_name="enriched_leads.csv",
            mime="text/csv",
            type="primary",
        )

        summary_columns = [
            "name",
            "company",
            "city",
            "state",
            "lead_score",
            "lead_priority",
            "enrichment_confidence",
            "recommended_action",
            "top_reason",
        ]

        available_summary_columns = [
            col for col in summary_columns if col in output_df.columns
        ]

        tab1, tab2 = st.tabs(["Summary", "Full Output"])

        with tab1:
            st.markdown("### Lead Prioritization Summary")

            summary_df = output_df[available_summary_columns]

            styled_summary = summary_df.style.map(
                style_priority,
                subset=["lead_priority"],
            )

            st.dataframe(styled_summary, use_container_width=True)

        with tab2:
            st.markdown("### Full Enriched Output")
            st.dataframe(output_df, use_container_width=True)


if __name__ == "__main__":
    main()