# Inbound Lead Orchestrator

A lightweight tool that transforms raw inbound leads into **enriched, prioritized, and outreach-ready opportunities**.

---

## Overview

This system takes a CSV of inbound leads and:

- Enriches them using public APIs  
- Scores and prioritizes leads  
- Generates actionable insights  
- Drafts personalized outreach emails  

---

## APIs Used

- **Wikipedia API** → Company context (what the company does)
- **U.S. Census API** → Market context (population, income)

---

## Email Generation (Two Pathways)

### AI-Enhanced (Primary)
- Uses enrichment + scoring context
- Generates natural, human-like outreach emails
- Requires `OPENAI_API_KEY`

### Fallback (Safe Mode)
- Rule-based templates
- Still uses company + market signals
- Ensures the system always works (no crashes)

---

## Input

CSV format: `name,email,company,property_address,city,state,country`

---

## Output

Each lead includes:

- `lead_score` + `lead_priority`  
- `enrichment_confidence`  
- `recommended_action`  
- `sales_insights`  
- `outreach_email`  

---

## Run the Tool

### CLI

```bash
python -m scripts.run_once
```

Input: scripts/sample_input.csv  
Output: data/output/enriched_leads.csv  

### Streamlit UI

streamlit run app/ui/streamlit_app.py  

- Upload CSV  
- Click Process Leads  
- Download results  

### Enable AI Emails (Optional)

export OPENAI_API_KEY="your_api_key_here"  

If not set → system automatically uses fallback.  

---



