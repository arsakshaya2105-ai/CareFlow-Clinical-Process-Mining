CAREFLOW — DBT + BIGQUERY STARTER
=================================

Purpose
-------
This starter project cleans a synthetic hospital event log for process-mining
analysis. It is designed to fail visibly when common data-quality problems are
found. It is not a production clinical system and must not be used with real,
identifiable patient data.

1. Before you start
-------------------
You need a Google Cloud project with BigQuery enabled, a raw table named
careflow_dataset.hospital_events, permission to create tables/views in a target
dataset, Python, and the Google Cloud CLI. The input table should have these
columns: Case_ID, Event_ID, Activity_Name, Timestamp, Department,
Patient_Category, Doctor_ID, Activity_Status.

2. Install dbt
--------------
Windows (PowerShell):
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  python -m pip install --upgrade pip
  python -m pip install dbt-bigquery

macOS/Linux:
  python3 -m venv .venv
  source .venv/bin/activate
  python -m pip install --upgrade pip
  python -m pip install dbt-bigquery

Check: dbt --version

3. Authenticate to Google Cloud
-------------------------------
  gcloud auth login
  gcloud auth application-default login
  gcloud config set project YOUR_PROJECT_ID

Enable the BigQuery API if prompted. Make sure the signed-in account has the
required BigQuery permissions.

4. Configure the connection
---------------------------
Copy profiles.yml.example to:
  Windows: %USERPROFILE%\.dbt\profiles.yml
  macOS/Linux: ~/.dbt/profiles.yml

Replace YOUR_PROJECT_ID and YOUR_DATASET_LOCATION. The location must match the
BigQuery dataset region exactly (for example, US or asia-south1). The output
dataset `careflow_dbt` must exist or your account must be allowed to create it.
Never commit your real profiles.yml or service-account keys.

5. Set the raw source
---------------------
Edit dbt_careflow/models/sources.yml and replace YOUR_PROJECT_ID. Confirm the
raw dataset and table names match your BigQuery table. If you used different
names, update `schema` and `tables` there.

6. Run the project
------------------
Open a terminal in the dbt_careflow directory and run each command:
  dbt debug
  dbt parse
  dbt run
  dbt test

`dbt debug` checks profile/connection details. `dbt parse` checks project and
model configuration. `dbt run` builds the staging view. `dbt test` runs the
column tests and SQL checks in the tests directory. A test query returns rows
when it detects a problem; dbt reports that test as a failure. Fix the source
data/configuration rather than deleting the test just to get a green result.

Checks included
---------------
- Source table is not empty.
- Required case/event/activity fields are not blank.
- Every source timestamp can be parsed.
- Event_ID is present and unique in the raw input.
- The staging view is not empty.
- Staged identifiers/activity/timestamps are not null and Event_ID is unique.

Important behavior
------------------
The staging model excludes rows missing Case_ID, Event_ID, Activity_Name, or a
parseable timestamp, and keeps one row per Event_ID. The source-level tests are
intended to catch those defects before cleaning hides them. Optional fields such
as Department or Doctor_ID may be blank because some workflows do not record
them for every event.

Troubleshooting
---------------
- Not found: confirm project, dataset, table, and region.
- Permission denied: ask the project owner to grant BigQuery job and data access.
- Invalid timestamp test: inspect Timestamp values and standardize them.
- Duplicate Event_ID test: create stable unique IDs or resolve duplicates in
the source; don't rely on staging deduplication to silently hide them.
- `data_tests` config error on an older dbt version: update dbt-bigquery, or
  change `data_tests:` to `tests:` in staging.yml if required by your version.
- If source test fails, query the raw table directly to inspect the returned
  offending rows. Test SQL files are deliberately written to return bad rows.

Academic integrity
------------------
This is a project-specific starter template. Adapt the comments and report to
what you actually configured, explain the choices in your own words, and cite
any external material you use. No tool can guarantee a document will pass every
AI-writing or plagiarism detector; detectors can produce false positives. The
reliable approach is to understand, verify, and honestly document your work.
