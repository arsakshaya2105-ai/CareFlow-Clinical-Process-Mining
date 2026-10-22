"""CareFlow process discovery.

Primary engine: PM4Py directly-follows graph (DFG) discovery.
Fallback: a pandas + NetworkX graph when PM4Py is not installed, so the
pipeline can still be exercised offline. The summary clearly records which
engine produced the map; fallback output must not be described as PM4Py output.

From project root:
    python process_mining/discover_process.py

Optional:
    python process_mining/discover_process.py --input data/careflow_cleaned_event_logs.csv
    python process_mining/discover_process.py --require-pm4py

Install full dependencies:
    python -m pip install pandas pm4py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError as exc:
    raise SystemExit(
        "ERROR: pandas is missing. Install it with:\n"
        "  python -m pip install pandas pm4py networkx matplotlib"
    ) from exc

try:
    import pm4py  # optional at import time; required for PM4Py discovery mode
except ImportError:
    pm4py = None

ROOT = Path(__file__).resolve().parents[1]
INPUT_CANDIDATES = [
    ROOT / "data" / "careflow_cleaned_event_logs.csv",
    ROOT / "data" / "cleaned_event_logs.csv",
    ROOT / "data" / "synthetic_event_logs.csv",
    ROOT / "data" / "synthetic_event_logs(1).csv",
]
DEFAULT_OUTPUT_DIR = ROOT / "process_mining" / "outputs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover the CareFlow event-log process.")
    parser.add_argument("--input", type=Path, help="Path to input event-log CSV.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
                        help="Directory for generated maps and reports.")
    parser.add_argument("--require-pm4py", action="store_true",
                        help="Fail instead of using offline fallback if PM4Py is unavailable.")
    return parser.parse_args()


def find_input(explicit_path: Path | None) -> Path:
    if explicit_path:
        path = explicit_path.expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Input CSV not found: {path}")
        return path
    for path in INPUT_CANDIDATES:
        if path.is_file():
            return path
    expected = "\n".join(f"  - {p}" for p in INPUT_CANDIDATES)
    raise FileNotFoundError(
        "Cleaned event-log CSV not found. Put it in the project's data folder, "
        "or pass --input PATH. Checked:\n" + expected
    )


def canonicalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    aliases = {
        "case_id": ["case_id", "case id", "case:concept:name", "caseid"],
        "event_id": ["event_id", "event id", "eventid"],
        "activity_name": ["activity_name", "activity name", "concept:name", "activity"],
        "event_timestamp": ["event_timestamp", "timestamp", "time:timestamp", "event time"],
    }
    lowered = {str(col).strip().lower(): col for col in df.columns}
    rename = {}
    for target, names in aliases.items():
        for name in names:
            if name in lowered:
                rename[lowered[name]] = target
                break
    return df.rename(columns=rename)


def load_and_clean(input_path: Path):
    df = pd.read_csv(input_path)
    original_rows = len(df)
    df.columns = [str(c).strip() for c in df.columns]
    df = canonicalize_columns(df)

    required = ["case_id", "activity_name", "event_timestamp"]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required column(s): {missing}. Available columns: {list(df.columns)}"
        )

    for col in ["case_id", "activity_name", "event_id"]:
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()

    df["activity_name"] = (
        df["activity_name"].astype("string")
        .str.lower().str.replace(r"\s+", " ", regex=True).str.strip()
    )
    df["event_timestamp"] = pd.to_datetime(df["event_timestamp"], errors="coerce", utc=True)

    invalid_timestamps = int(df["event_timestamp"].isna().sum())
    invalid_required_mask = (
        df["case_id"].isna() | df["case_id"].eq("")
        | df["activity_name"].isna() | df["activity_name"].eq("")
        | df["event_timestamp"].isna()
    )
    removed_required = int(invalid_required_mask.sum())
    df = df.loc[~invalid_required_mask].copy()

    duplicate_event_rows = 0
    if "event_id" in df.columns:
        has_id = df["event_id"].notna() & df["event_id"].ne("")
        duplicate_mask = has_id & df["event_id"].duplicated(keep="first")
        duplicate_event_rows = int(duplicate_mask.sum())
        df = df.loc[~duplicate_mask].copy()

    sort_columns = ["case_id", "event_timestamp"]
    if "event_id" in df.columns:
        sort_columns.append("event_id")
    df = df.sort_values(sort_columns, kind="stable").reset_index(drop=True)
    if df.empty:
        raise ValueError("No valid events remain after cleaning; cannot discover a process.")

    quality = {
        "input_rows": original_rows,
        "invalid_timestamp_rows": invalid_timestamps,
        "removed_required_rows": removed_required,
        "duplicate_event_id_rows_removed": duplicate_event_rows,
    }
    return df, quality


def build_dfg_from_dataframe(df: pd.DataFrame):
    """Return edge counts and start/end activity counts without PM4Py."""
    edges: dict[tuple[str, str], int] = {}
    starts: dict[str, int] = {}
    ends: dict[str, int] = {}
    for _, case_df in df.groupby("case_id", sort=False):
        activities = case_df["activity_name"].tolist()
        if not activities:
            continue
        starts[activities[0]] = starts.get(activities[0], 0) + 1
        ends[activities[-1]] = ends.get(activities[-1], 0) + 1
        for source, target in zip(activities, activities[1:]):
            edges[(source, target)] = edges.get((source, target), 0) + 1
    return edges, starts, ends


def save_fallback_map(edges, starts, ends, map_path: Path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import networkx as nx
    except ImportError as exc:
        raise RuntimeError(
            "PM4Py is unavailable and fallback dependencies are missing. Install with:\n"
            "  python -m pip install pandas pm4py networkx matplotlib"
        ) from exc

    graph = nx.DiGraph()
    for activity, count in starts.items():
        graph.add_node(activity, start_count=count)
    for activity, count in ends.items():
        graph.add_node(activity, end_count=count)
    for (source, target), count in edges.items():
        graph.add_edge(source, target, weight=count)

    figure_width = max(10, min(18, 1.5 * max(1, graph.number_of_nodes())))
    fig, ax = plt.subplots(figsize=(figure_width, 7))
    positions = nx.spring_layout(graph, seed=42, k=1.3)
    labels = {node: node.replace(" ", "\n") for node in graph.nodes}
    nx.draw_networkx_nodes(graph, positions, node_size=2600, ax=ax)
    nx.draw_networkx_labels(graph, positions, labels=labels, font_size=8, ax=ax)
    nx.draw_networkx_edges(
        graph, positions, arrows=True, arrowsize=18,
        connectionstyle="arc3,rad=0.08", node_size=2600, ax=ax
    )
    edge_labels = {(u, v): data["weight"] for u, v, data in graph.edges(data=True)}
    nx.draw_networkx_edge_labels(graph, positions, edge_labels=edge_labels, font_size=8, ax=ax)
    ax.set_title("CareFlow Directly-Follows Process Map (offline fallback)\nEdge labels = transition counts")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(map_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    args = parse_args()
    input_path = find_input(args.input)
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if pm4py is None and args.require_pm4py:
        raise RuntimeError(
            "PM4Py is not installed in this Python environment. Install it with:\n"
            "  python -m pip install pandas pm4py\n"
            "If package installation fails because of network/DNS, connect to a working "
            "network and retry. This run was stopped because --require-pm4py was set."
        )

    df, quality = load_and_clean(input_path)
    map_path = output_dir / "actual_process_map.png"

    if pm4py is not None:
        event_log = pm4py.format_dataframe(
            df.copy(), case_id="case_id", activity_key="activity_name",
            timestamp_key="event_timestamp"
        )
        dfg, start_activities, end_activities = pm4py.discover_dfg(event_log)
        pm4py.save_vis_dfg(dfg, start_activities, end_activities, str(map_path))
        discovery_engine = f"PM4Py {getattr(pm4py, '__version__', 'version unknown')}"
        transition_count = len(dfg)
        starts = dict(start_activities)
        ends = dict(end_activities)
    else:
        dfg, start_activities, end_activities = build_dfg_from_dataframe(df)
        save_fallback_map(dfg, start_activities, end_activities, map_path)
        discovery_engine = "Offline fallback (pandas + NetworkX; NOT PM4Py)"
        transition_count = len(dfg)
        starts, ends = start_activities, end_activities

    activity_frequency = (
        df.groupby("activity_name")
        .agg(event_count=("activity_name", "size"), case_count=("case_id", "nunique"))
        .reset_index()
        .sort_values(["event_count", "activity_name"], ascending=[False, True])
    )
    activity_frequency.to_csv(output_dir / "activity_frequency.csv", index=False)

    repeated = df.groupby(["case_id", "activity_name"]).size().reset_index(name="occurrences")
    repeated = repeated[repeated["occurrences"] > 1].sort_values(
        ["occurrences", "case_id"], ascending=[False, True]
    )
    repeated.to_csv(output_dir / "repeated_activities.csv", index=False)

    per_case = df.groupby("case_id", sort=False)
    first_activities = per_case.first()["activity_name"]
    last_activities = per_case.last()["activity_name"]
    repeated_triage_cases = int(
        repeated.loc[repeated["activity_name"].str.contains("triage", na=False), "case_id"].nunique()
    )
    repeated_consult_cases = int(
        repeated.loc[repeated["activity_name"].str.contains("consult", na=False), "case_id"].nunique()
    )

    summary_path = output_dir / "process_summary.txt"
    summary_lines = [
        "CareFlow Process Discovery Summary",
        "==================================",
        f"Discovery engine: {discovery_engine}",
        f"Input file: {input_path}",
        f"Input rows: {quality['input_rows']}",
        f"Rows with invalid timestamps: {quality['invalid_timestamp_rows']}",
        f"Rows with missing required fields removed: {quality['removed_required_rows']}",
        f"Duplicate event-ID rows removed: {quality['duplicate_event_id_rows_removed']}",
        f"Rows used for discovery: {len(df)}",
        f"Unique cases: {df['case_id'].nunique()}",
        f"Unique activities: {df['activity_name'].nunique()}",
        f"Directly-follows transition types: {transition_count}",
        f"Cases starting with registration: {int(first_activities.str.contains('registration', case=False, na=False).sum())}",
        f"Cases ending with discharge: {int(last_activities.str.contains('discharge', case=False, na=False).sum())}",
        f"Cases with repeated triage: {repeated_triage_cases}",
        f"Cases with repeated consultation-related activity: {repeated_consult_cases}",
        "",
        "Outputs:",
        f"  {map_path}",
        f"  {output_dir / 'activity_frequency.csv'}",
        f"  {output_dir / 'repeated_activities.csv'}",
        f"  {summary_path}",
        "",
        "Interpretation note: repeated activities are not automatically errors; review context.",
    ]
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    print("CareFlow process discovery completed.")
    print(f"Discovery engine: {discovery_engine}")
    print(f"Input: {input_path}")
    print(f"Cases: {df['case_id'].nunique()} | Events: {len(df)}")
    print(f"Activities: {df['activity_name'].nunique()} | Transition types: {transition_count}")
    print(f"Process map: {map_path}")
    print(f"Activity report: {output_dir / 'activity_frequency.csv'}")
    print(f"Repeated activity report: {output_dir / 'repeated_activities.csv'}")
    print(f"Summary: {summary_path}")
    if pm4py is None:
        print("NOTE: PM4Py was unavailable; the map used the clearly labelled offline fallback.")
        print("For actual PM4Py discovery, install PM4Py and rerun this script.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
