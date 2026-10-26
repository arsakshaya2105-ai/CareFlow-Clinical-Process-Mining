# CareFlow – Process Mining (PM4Py)

## Files
- `process_mining/discover_process.py`: executable process-discovery script
- `synthetic_event_logs.csv`: input event-log dataset
- `requirements.txt`: Python dependencies
- `outputs/`: created automatically when the script runs

## Requirements
Install Python 3.10 or newer and VS Code. During Python installation on Windows, enable **Add Python to PATH**.

## Run on Windows
1. Extract this ZIP file.
2. Open the extracted `careflow_process_mining` folder in VS Code.
3. Open **Terminal > New Terminal**.
4. Check Python: `py --version`
5. Install dependencies: `py -m pip install -r requirements.txt`
6. Run the script: `py process_mining/discover_process.py`

If `py` is not recognized, try `python --version`, then use `python -m pip install -r requirements.txt` and `python process_mining/discover_process.py`.

## Output
The script creates an `outputs` folder containing CSV reports for activity counts, observed process transitions, waiting-time estimates between consecutive events, and patient journey durations. It also attempts to create `process_map.png`. PNG visualization may require Graphviz to be installed separately; the CSV reports do not depend on that visualization succeeding.

## Dataset columns used
`Case_ID`, `Activity_Name`, and `Timestamp`. Other columns in the dataset are retained in the input file but are not required for process discovery.

Note: the dataset contains synthetic/mock hospital events. Findings should be described as analysis of the provided synthetic data, not real patient outcomes.
