# CareFlow dbt normalization models (BigQuery)

## Models
- `stg_hospital_events`: casts raw fields, trims identifiers, parses timestamps with `SAFE_CAST`, excludes rows missing required fields or with invalid timestamps, deduplicates by `event_id`, normalizes whitespace/case, and adds `event_date`.
- `int_activity_events`: maps common activity label variants to canonical labels and calculates minutes since the previous event within each case.

## Configure before running
1. Edit `dbt_careflow/models/sources.yml` and replace `YOUR_PROJECT_ID` with your Google Cloud project ID. Confirm `schema: careflow_dataset` matches the actual raw BigQuery dataset and `hospital_events` matches the table name.
2. Ensure your dbt profile (profile name `dbt_careflow`) has the correct project, dataset, location (for example `asia-south1`), and OAuth/service-account configuration.
3. Run from the `dbt_careflow` directory:

```powershell
dbt debug
dbt parse
dbt run
dbt test
```

## Input schema expected
The source table is expected to have `Case_ID`, `Event_ID`, `Activity_Name`, `Timestamp`, `Department`, `Patient_Category`, `Doctor_ID`, and `Activity_Status`. If your raw table already uses lowercase names, update the column references in `stg_hospital_events.sql` accordingly.

## Notes
- BigQuery `SAFE_CAST` yields NULL for unparseable timestamps; those rows are excluded from the staging model.
- Event IDs are assumed globally unique; duplicates keep the earliest timestamp/case row.
- The canonical activity mapping is a starting point. Update it to match actual labels in your source data.
- These files have not been run against your BigQuery account; successful `dbt run`/`dbt test` requires valid credentials and the correct source table.
