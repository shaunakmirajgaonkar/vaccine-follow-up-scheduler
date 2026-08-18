# 💉 VaxFollow Local

Privacy-conscious, local-first vaccine follow-up scheduling decision-support workspace.

## Features
- Missed/delayed follow-up screening from locally supplied dates and statuses
- 0–100 transparent operational follow-up score
- Routine / Attention / High Priority / Urgent Review classification
- Human follow-up queue and reminder workflow support
- Dose-level explanations
- Plotly analytics
- CSV validation and scored export
- Synthetic demonstration dataset
- No external APIs or cloud submission

## Safety boundary
This is not a clinical decision system. It does not prescribe vaccines, determine eligibility, or generate authoritative catch-up schedules. Verify current official guidance and any catch-up action with a qualified healthcare professional.

## Run
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python validate_data.py
python -m streamlit run app.py
```

## Required CSV
```text
record_id, person_code, age_band, dose_name, vaccine_group, due_date, administered_date, status, reminder_status, preferred_language, care_setting, follow_up_contact_available, high_priority_flag, notes
```
