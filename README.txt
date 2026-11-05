CareFlow analysis deliverables

1) process_mining/conformance_check.py
   Configurable rule-based conformance checker for the reference pathway.
   It outputs case-level results, transition-level results, and summary CSV.
   It is NOT PM4Py token replay. The reference rules are documented in the script.

2) sql/careflow_operational_kpis_bigquery.sql
   BigQuery Standard SQL templates for journey duration, activity volume,
   repeated activities, inter-event gaps, and start/end validation.
   Replace the placeholder project/dataset/table before running in BigQuery.

3) outputs/
   Contains results generated from the supplied cleaned CSV. The KPI calculations
   were executed locally using SQLite-compatible SQL over the CSV, not in the
   user's BigQuery project. BigQuery execution remains pending until credentials,
   dataset, and table are configured.

Interpretation caution:
Event-to-event elapsed time is not necessarily queue waiting time. Repeated
activities and conformance deviations need clinical/process-owner review.
