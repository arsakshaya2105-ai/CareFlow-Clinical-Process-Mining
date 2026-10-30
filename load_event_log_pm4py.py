#!/usr/bin/env python
"""Load CareFlow cleaned CSV into PM4Py and export a native XES event log."""
from pathlib import Path
import argparse
import sys

try:
    import pandas as pd
    import pm4py
except ImportError as exc:
    print(f"Missing dependency: {exc}")
    print("Install with: python -m pip install pandas pm4py")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/careflow_cleaned_event_logs.csv")
    parser.add_argument("--output", default="process_mining/outputs/careflow_event_log.xes")
    args = parser.parse_args()
    source, output = Path(args.input), Path(args.output)
    if not source.exists():
        raise FileNotFoundError(f"Input CSV not found: {source.resolve()}")

    df = pd.read_csv(source)
    df.columns = [c.strip().lower() for c in df.columns]
    required = {"case_id", "activity_name", "event_timestamp"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df["case_id"] = df["case_id"].astype("string").str.strip()
    df["activity_name"] = df["activity_name"].astype("string").str.strip().str.replace(r"\\s+", " ", regex=True).str.lower()
    df["event_timestamp"] = pd.to_datetime(df["event_timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["case_id", "activity_name", "event_timestamp"])
    df = df[(df["case_id"] != "") & (df["activity_name"] != "")]
    if df.empty:
        raise ValueError("No valid events remain after validation.")
    df = df.sort_values(["case_id", "event_timestamp"], kind="stable")

    formatted = pm4py.format_dataframe(df, case_id="case_id",
                                      activity_key="activity_name",
                                      timestamp_key="event_timestamp")
    event_log = pm4py.convert_to_event_log(formatted)
    output.parent.mkdir(parents=True, exist_ok=True)
    pm4py.write_xes(event_log, str(output))
    print("PM4Py event-log load completed successfully.")
    print(f"Events: {len(formatted):,}")
    print(f"Cases: {formatted['case_id'].nunique():,}")
    print(f"Activities: {formatted['activity_name'].nunique():,}")
    print(f"XES output: {output.resolve()}")

if __name__ == "__main__":
    main()
