# Inbound Lead Orchestrator

A lightweight tool that turns raw inbound leads into **enriched, scored, and outreach-ready opportunities**.

---

## APIs & Enrichment
The orchestrator leverages external data sources to build a profile for every lead:

* **Wikipedia API**: Enriches company context to identify industry and core business activities.
* **U.S. Census API**: Provides market context using population and income data based on the property location.

---

## Key Outputs

For each lead, the tool generates a structured output ready for CRM import/SDR review:

| Category | Fields |
| :--- | :--- |
| **Scoring** | `lead_score`, `lead_priority` |
| **Validation** | `enrichment_confidence` |
| **Strategy** | `recommended_action`, `score_reasons`, `sales_insights` |
| **Outreach** | `outreach_email` |

---

## Email Generation Logic

The tool features a resilient outreach workflow with two distinct paths:

1.  **AI-Enhanced Path**: If `OPENAI_API_KEY` is configured, the tool uses LLMs to convert structured enrichment data into a natural, personalized outreach email.
2.  **Fallback Path**: If the API key is missing or the AI call fails, the tool utilizes deterministic templates to ensure the pipeline never breaks.

---

## Running the Tool

### 1. Streamlit UI

Best for manual uploads and visual inspection.
* Upload lead CSVs.
* Preview scored results in real-time.
* Download the enriched CSV.

**Run locally:**
```bash
streamlit run app/ui/streamlit_app.py
```
*Note: Expected CSV columns: `name`, `email`, `company`, `property_address`, `city`, `state`, `country`.*

### 2. GitHub Actions Automation

The repository includes a workflow for automated hands-off processing:
* **Schedule**: Runs daily at 9:00 AM UTC.
* **Manual**: Can be triggered via `GitHub Repo → Actions → Scheduled Lead Processing`.
* **Artifacts**: Generates and stores `enriched_leads.csv` in the workflow run.

### 3. Local CLI Option

Run the backend pipeline directly from the terminal:
```bash
python -m scripts.run_once
```

---

## Setup & Installation

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure Environment (Optional):**
    To enable AI-generated emails:
    ```bash
    export OPENAI_API_KEY="your_api_key_here"
    ```

3.  **Run Tests:**
    ```bash
    pytest
    ```
    *The suite covers scoring behavior, fallback logic, and pipeline processing.*

---

## Project Structure

* `app/`: Core application code, including API clients, models, services, utilities, and the Streamlit UI.
* `scripts/`: Sample input CSV and CLI runner.
* `tests/`: Tests for scoring, fallback outreach, and pipeline processing.
* `.github/workflows/`: Scheduled automation for running the pipeline.
* Runtime output: Enriched CSV is generated at `data/output/enriched_leads.csv` locally, or uploaded as a GitHub Actions artifact when run in CI.

---

> **Note:** In a production environment, the scheduled input can be mapped to a CRM export (Salesforce/HubSpot), a Google Sheet, or an S3 bucket trigger.
```