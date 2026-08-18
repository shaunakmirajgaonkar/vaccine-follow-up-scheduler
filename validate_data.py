from pathlib import Path
import pandas as pd
REQUIRED=['record_id','person_code','age_band','dose_name','vaccine_group','due_date','administered_date','status','reminder_status','preferred_language','care_setting','follow_up_contact_available','high_priority_flag','notes']
p=Path('data/vaccine_follow_up_registry.csv')
df=pd.read_csv(p)
missing=[c for c in REQUIRED if c not in df.columns]
if missing: raise SystemExit(f'Missing required columns: {missing}')
if df.record_id.isna().any(): raise SystemExit('record_id contains missing values')
if df.record_id.duplicated().any(): raise SystemExit('record_id contains duplicates')
print(f'VALID: {len(df)} records, {len(df.columns)} columns')
print('No external services required.')
