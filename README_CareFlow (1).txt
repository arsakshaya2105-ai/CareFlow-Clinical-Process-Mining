Care-flow: Clinical Pathway Process Mining

> A healthcare operations analytics project that uses process mining to uncover patient-flow bottlenecks, repeated activities, and deviations from intended clinical pathways.

 Overview

Hospital dashboards often report average Emergency Room (ER) waiting times, but those averages may not explain the sequence of events that causes delays. **CareFlow** analyzes timestamped patient activity logs to reconstruct patient journeys, discover the actual process flow, measure time between activities, and identify potential operational bottlenecks.

The project follows the CareFlow concept described in the *Infotact Solutions Project Document – Advanced Data Analytics (Vol. II)*. It is intended as a four-week prototype using simulated hospital event data.

Project Objectives

- Generate synthetic Electronic Health Record (EHR)-style event logs.
- Store raw event data in Google BigQuery.
- Clean and standardize event records with dbt.
- Discover actual patient pathways using PM4Py.
- Measure transition times and identify repeated activities or possible rework.
- Compare observed journeys with a defined ideal pathway.
- Present operational metrics and process insights in Microsoft Power BI.

 Technology Stack

| Technology | Role |
|---|---|
| Python | Generate synthetic event logs and perform analysis |
| Google BigQuery | Store and query chronological event data |
| dbt | Clean, standardize, and test event-log data |
| PM4Py | Discover process models and support conformance analysis |
| SQL | Calculate activity transitions and operational KPIs |
| Microsoft Power BI | Visualize process flows, bottlenecks, and KPIs |
| Git and GitHub | Version control, collaboration, issues, and project documentation |
| GitHub Actions (optional) | Run automated tests on pushes and pull requests |

 Architecture

```text
Synthetic EHR Event Generator (Python)
                 |
                 v
        Raw Event Logs
                 |
                 v
        Google BigQuery
                 |
                 v
       dbt Cleaning Models
                 |
                 v
       Standardized Event Log
            /          \
           v            v
        PM4Py       SQL / Python
   Process Discovery  KPI Analysis
           \            /
            v          v
       Validated Process Insights
                 |
                 v
          Power BI Dashboard
```

> This diagram describes the intended prototype architecture. Cloud connections, credentials, scheduled runs, and dashboard refreshes must be configured separately.

Event Log Design

Each row represents one activity in a patient's journey. The minimum fields are:

| Field | Description |
|---|---|
| `Case_ID` | Identifier for a patient journey; use synthetic IDs in this project |
| `Activity_Name` | Activity performed, such as Registration, Triage, X-Ray, Consultation, or Discharge |
| `Timestamp` | Time at which the event occurred |

Additional fields may be added when useful, such as `Department`, `Doctor_ID`, `Activity_Status`, and `Event_ID`.

Example

| Case_ID | Activity_Name | Timestamp |
|---|---|---|
| P001 | Registration | 10:00 |
| P001 | Triage | 10:05 |
| P001 | Doctor Consultation | 10:20 |
| P001 | X-Ray | 10:35 |
| P001 | Triage | 10:50 |
| P001 | Doctor Consultation | 11:00 |
| P001 | Discharge | 11:30 |

The repeated triage activity is an example of a potential rework loop to investigate—not proof of an error or its cause. These rows are illustrative synthetic data, not real patient records.

Core Modules

 1. Synthetic Event Generation
Create reproducible mock patient journeys, including normal paths, alternative paths, delays, and deliberately introduced loops for testing.

2. Data Warehouse and Transformation
Load raw events into BigQuery. Use dbt to standardize field names and types, handle invalid records, and test data quality.

3. Process Discovery
Use PM4Py to discover an as-is process model from the standardized event log. Review the major routes, variants, and repeated activities.

4. Bottleneck Analysis
Use SQL and Python to calculate elapsed time between consecutive events and summarize transitions by activity or other available dimensions.

Metric note: A timestamp per event supports elapsed-time calculations between events. Accurate service waiting time may require additional events or timestamps, such as arrival, service start, and service completion.

5. Conformance Checking
Define an expected clinical pathway and compare observed event sequences against its rules. Document how deviations are identified and validated.

6. Power BI Dashboard
Build views for process flow, transition times, repeated activities, pathway compliance, and relevant operational KPIs. Add filters only for dimensions present in the dataset.

Key Performance Indicators

- Average ER length of stay: Elapsed time from the defined start event to the defined end event.
- Average transition time: Average elapsed time between consecutive activities.
- Activity frequency: Number of occurrences of each activity.
- Rework rate: Percentage of journeys containing a specified repeated activity or loop.
- Pathway compliance rate: Percentage of journeys satisfying the defined pathway rules.
- Patient throughput: Number of completed journeys in a selected time period.

Define each KPI precisely and validate it against sample cases before presenting it as a result.

Four-Week Development Plan

| Week | Focus | Expected Deliverables |
|---|---|---|
| 1 | Event-log generation and warehouse setup | Python generator, BigQuery raw table, initial dbt project |
| 2 | Event normalization and process discovery | Clean event-log models, data-quality checks, first PM4Py process map |
| 3 | Bottleneck analysis and dashboard | Transition-time calculations, Power BI prototype |
| 4 | Conformance checking and final validation | Pathway comparison, refined dashboard, tests, documentation, final presentation |

These are planned deliverables. Update this README as features are implemented and verified.

Repository Structure

```text
CareFlow-Clinical-Process-Mining/
├── data/
│   └── README.md                 # Data instructions; avoid committing sensitive data
├── src/
│   └── generate_event_logs.py    # Synthetic event generator
├── dbt_careflow/
│   ├── models/                   # dbt transformation models
│   └── dbt_project.yml
├── process_mining/
│   ├── discover_process.py       # PM4Py process discovery
│   └── conformance_check.py      # Pathway conformance logic
├── sql/
│   └── kpi_queries.sql           # BigQuery KPI queries
├── dashboard/
│   └── README.md                 # Power BI setup and screenshots
├── tests/
│   └──                           # Data and analytics tests
├── docs/
│   └── architecture.md
├── .github/
│   └── workflows/
│       └── tests.yml             # Optional CI workflow
├── .gitignore
├── requirements.txt
└── README.md
```

This is a suggested layout. Rename or remove paths to match the files actually present in your repository.

 Getting Started

 Prerequisites

- Python version compatible with the dependencies you select
- Git
- A Google Cloud project and BigQuery access, if running the warehouse pipeline
- dbt configured for BigQuery, if using dbt
- Power BI Desktop, if building the dashboard

 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/CareFlow-Clinical-Process-Mining.git
cd CareFlow-Clinical-Process-Mining
```

Replace `YOUR_USERNAME` with your GitHub username.

 2. Create a Python environment

```bash
python -m venv .venv
```

Activate it:

Windows PowerShell
```powershell
.\.venv\Scripts\Activate.ps1
```

macOS / Linux
```bash
source .venv/bin/activate
```

3. Install dependencies

Once `requirements.txt` has been created and populated:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Example packages that may be required as the modules are implemented include `pandas`, `pm4py`, and `google-cloud-bigquery`. Add only the dependencies the project actually uses and pin tested versions.

4. Generate synthetic event data

After implementing the generator, run:

```bash
python src/generate_event_logs.py
```

Update the command if your script uses different arguments or output paths.

#5.Run tests

After adding tests:

```bash
python -m pytest tests/
```

6. Configure BigQuery and dbt

Create the required BigQuery dataset and configure dbt for your Google Cloud project. Follow your organization's approved authentication process. Do not put credentials directly in source files or commit them to GitHub.

7. Run process discovery

After the event log is cleaned and exported to the format expected by your PM4Py script, run the implemented discovery command. Document the actual command and expected output here once verified.

8. Open the dashboard

Open the Power BI project file in `dashboard/` after it has been created, and configure the appropriate data connection and refresh settings.

> The commands above are a setup template. They will work only after the referenced scripts, dependencies, configuration, and project files have been created.

Git and GitHub Workflow

Use feature branches and pull requests to keep development organized.

```bash
git switch -c feature/event-log-generator
# Create or edit files and run relevant tests
git add .
git commit -m "Add synthetic event log generator"
git push -u origin feature/event-log-generator
```

Then open a pull request on GitHub, review the changes, and merge when tests pass. Create separate branches for dbt transformations, process discovery, KPI analysis, and dashboard work.

Testing and Validation Checklist

- [ ] Synthetic events have valid case IDs, activity names, and timestamps.
- [ ] Events are correctly ordered within each case.
- [ ] Missing values, duplicates, and invalid timestamps are handled intentionally.
- [ ] dbt models and data-quality tests pass.
- [ ] PM4Py creates a process model from the cleaned event log.
- [ ] Transition-time calculations match manually checked sample cases.
- [ ] Repeated activities and conformance rules are tested with known examples.
- [ ] Power BI metrics agree with the validated source data.
- [ ] README commands and screenshots match the current implementation.

 Responsible Data Use

- Use synthetic data for development, demonstrations, and public portfolio examples.
- Do not commit real patient records, personally identifiable information, protected health information, credentials, or confidential hospital data.
- Apply appropriate access controls and approved handling procedures if working with authorized real-world data.
- Treat detected loops or deviations as investigation signals, not automatic proof of clinical error.
- Validate any operational recommendation with qualified hospital stakeholders before real-world use.

Current Status

Planned prototype. Update this section with implemented features, test results, dashboard screenshots, and known limitations as the project progresses. Do not describe planned features as completed until they have been tested.

Future Enhancements

- Add event-level data-quality and schema validation.
- Compare multiple process-discovery methods.
- Add time-based and department-based process variants where data supports them.
- Automate tests through GitHub Actions.
- Add reproducible sample outputs and dashboard screenshots.
- Evaluate operational changes using clearly defined before-and-after measures.

License

Choose and add a license before allowing others to reuse or distribute this project. If no license has been selected, state that the repository is not yet licensed.

---

Care-flow— Turning timestamped patient events into clearer clinical pathway insights.