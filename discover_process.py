"""
CareFlow - Clinical Pathway Process Mining
Discover a Directly-Follows Graph (DFG) from timestamped hospital event logs.

Expected CSV columns:
  Case_ID, Activity_Name, Timestamp
Optional columns are preserved in the original input but are not required for discovery.
"""
from pathlib import Path
import sys
import pandas as pd

try:
    import pm4py
except ImportError:
    print("PM4Py is not installed. Run: python -m pip install -r requirements.txt")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
INPUT_CSV = ROOT / "synthetic_event_logs.csv"
OUTPUT_DIR = ROOT / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

CASE_COL = "Case_ID"
ACTIVITY_COL = "Activity_Name"
TIME_COL = "Timestamp"


def main():
    if not INPUT_CSV.exists():
        print(f"ERROR: Dataset not found: {INPUT_CSV}")
        print("Place synthetic_event_logs.csv in the project root folder.")
        sys.exit(1)

    df = pd.read_csv(INPUT_CSV)
    required = [CASE_COL, ACTIVITY_COL, TIME_COL]
    missing = [c for c in required if c not in df.columns]
    if missing:
        print("ERROR: Required column(s) missing:", ", ".join(missing))
        print("Columns found:", ", ".join(map(str, df.columns)))
        sys.exit(1)

    df = df.dropna(subset=required).copy()
    df[TIME_COL] = pd.to_datetime(df[TIME_COL], errors="coerce")
    df = df.dropna(subset=[TIME_COL])
    df[CASE_COL] = df[CASE_COL].astype(str)
    df[ACTIVITY_COL] = df[ACTIVITY_COL].astype(str)
    df = df.sort_values([CASE_COL, TIME_COL])

    if df.empty:
        print("ERROR: No valid event rows remain after cleaning.")
        sys.exit(1)

    print(f"Loaded {len(df):,} events from {df[CASE_COL].nunique():,} cases.")
    print("Discovering process model with PM4Py...")

    # Convert the dataframe to a PM4Py event log.
    event_log = pm4py.format_dataframe(
        df,
        case_id=CASE_COL,
        activity_key=ACTIVITY_COL,
        timestamp_key=TIME_COL,
    )

    # Discover a directly-follows graph: the observed activity-to-activity paths.
    dfg, start_activities, end_activities = pm4py.discover_dfg(event_log)

    transitions = pd.DataFrame(
        [
            {"From_Activity": source, "To_Activity": target, "Frequency": frequency}
            for (source, target), frequency in dfg.items()
        ],
        columns=["From_Activity", "To_Activity", "Frequency"],
    ).sort_values("Frequency", ascending=False)
    transitions.to_csv(OUTPUT_DIR / "process_transitions.csv", index=False)

    activity_counts = (
        df.groupby(ACTIVITY_COL)
        .size()
        .reset_index(name="Event_Count")
        .sort_values("Event_Count", ascending=False)
    )
    activity_counts.to_csv(OUTPUT_DIR / "activity_counts.csv", index=False)

    # Calculate elapsed time between consecutive events for each patient case.
    df["Next_Timestamp"] = df.groupby(CASE_COL)[TIME_COL].shift(-1)
    df["Next_Activity"] = df.groupby(CASE_COL)[ACTIVITY_COL].shift(-1)
    df["Wait_Minutes"] = (
        (df["Next_Timestamp"] - df[TIME_COL]).dt.total_seconds() / 60
    )
    waits = df.dropna(subset=["Next_Activity", "Wait_Minutes"])
    bottlenecks = (
        waits.groupby([ACTIVITY_COL, "Next_Activity"])["Wait_Minutes"]
        .agg(Transition_Count="count", Average_Wait_Minutes="mean",
             Median_Wait_Minutes="median", Maximum_Wait_Minutes="max")
        .reset_index()
        .rename(columns={ACTIVITY_COL: "From_Activity",
                         "Next_Activity": "To_Activity"})
        .sort_values("Average_Wait_Minutes", ascending=False)
    )
    bottlenecks.to_csv(OUTPUT_DIR / "transition_wait_times.csv", index=False)

    case_summary = (
        df.groupby(CASE_COL)
        .agg(Event_Count=(ACTIVITY_COL, "size"),
             Start_Time=(TIME_COL, "min"),
             End_Time=(TIME_COL, "max"))
        .reset_index()
    )
    case_summary["Journey_Duration_Minutes"] = (
        (case_summary["End_Time"] - case_summary["Start_Time"])
        .dt.total_seconds() / 60
    )
    case_summary.to_csv(OUTPUT_DIR / "patient_journey_summary.csv", index=False)

    # Try to create a PNG visualization. CSV outputs are still produced if Graphviz
    # or the visualization dependencies are not available.
    try:
        pm4py.save_vis_dfg(
            dfg, start_activities, end_activities,
            str(OUTPUT_DIR / "process_map.png")
        )
        print("Created process_map.png")
    except Exception as exc:
        print("Could not create process_map.png (optional visualization).")
        print("Details:", exc)
        print("The CSV analysis files were still generated.")

    print("\nDone! Results saved in:", OUTPUT_DIR)
    print("- process_transitions.csv: common activity-to-activity paths")
    print("- activity_counts.csv: event counts by activity")
    print("- transition_wait_times.csv: estimated waiting time between activities")
    print("- patient_journey_summary.csv: event count and journey duration per case")
    print("- process_map.png: visual process map, if Graphviz is available")


if __name__ == "__main__":
    main()
