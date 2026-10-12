#!/usr/bin/env python3
"""
CareFlow synthetic hospital event-log generator.

Creates fictional EHR-style event logs for process-mining development and testing.
Each row represents one activity event for one synthetic patient journey.

Default output:
    data/synthetic_event_logs.csv

Example:
    python src/generate_event_logs.py
    python src/generate_event_logs.py --cases 1000 --seed 7
    python src/generate_event_logs.py --cases 250 --output data/demo_events.csv

This script creates synthetic data only. Do not use it to generate, store, or
publish identifiable real patient information.
"""

from __future__ import annotations

import argparse
import csv
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable


ACTIVITIES = [
    "Registration",
    "Triage",
    "Doctor Consultation",
    "Laboratory Test",
    "X-Ray",
    "Treatment",
    "Discharge",
]

# Typical illustrative durations between activity events, in minutes.
# These are synthetic assumptions for testing—not clinical benchmarks.
DURATION_RANGES: dict[str, tuple[int, int]] = {
    "Registration": (2, 10),
    "Triage": (3, 20),
    "Doctor Consultation": (5, 45),
    "Laboratory Test": (10, 75),
    "X-Ray": (10, 60),
    "Treatment": (5, 90),
    "Discharge": (3, 25),
}

DEPARTMENTS = ["Emergency", "Radiology", "Laboratory"]
PATIENT_CATEGORIES = ["Low Acuity", "Moderate Acuity", "High Acuity"]


@dataclass(frozen=True)
class Event:
    """One synthetic event in a patient case."""

    case_id: str
    event_id: str
    activity_name: str
    timestamp: datetime
    department: str
    patient_category: str
    doctor_id: str
    event_status: str


def random_duration(activity: str, rng: random.Random) -> int:
    """Return a synthetic number of minutes before the next event."""
    low, high = DURATION_RANGES[activity]
    return rng.randint(low, high)


def choose_department(activity: str, rng: random.Random) -> str:
    """Assign a plausible department for the synthetic activity."""
    if activity == "X-Ray":
        return "Radiology"
    if activity == "Laboratory Test":
        return "Laboratory"
    return "Emergency"


def build_journey(
    case_number: int,
    arrival_time: datetime,
    rng: random.Random,
    rework_probability: float,
    delay_probability: float,
) -> list[Event]:
    """Build one synthetic patient journey, optionally including rework loops."""
    case_id = f"P{case_number:05d}"
    category = rng.choices(
        PATIENT_CATEGORIES, weights=[0.50, 0.35, 0.15], k=1
    )[0]
    doctor_id = f"D{rng.randint(1, 12):03d}"

    # Every case starts with registration and triage.
    journey = ["Registration", "Triage", "Doctor Consultation"]

    # A subset of cases receives a diagnostic activity.
    diagnostic_choice = rng.choices(
        ["none", "lab", "xray", "both"],
        weights=[0.20, 0.30, 0.25, 0.25],
        k=1,
    )[0]
    if diagnostic_choice == "lab":
        journey += ["Laboratory Test", "Doctor Consultation"]
    elif diagnostic_choice == "xray":
        journey += ["X-Ray", "Doctor Consultation"]
    elif diagnostic_choice == "both":
        if rng.random() < 0.5:
            journey += ["Laboratory Test", "X-Ray", "Doctor Consultation"]
        else:
            journey += ["X-Ray", "Laboratory Test", "Doctor Consultation"]

    # Add a deliberate loop to a portion of cases so process mining can detect it.
    if rng.random() < rework_probability:
        loop_target = rng.choice(["Triage", "Doctor Consultation"])
        insert_at = max(2, len(journey) - 1)
        journey.insert(insert_at, loop_target)

    # Treatment is optional; discharge ends every generated journey.
    if rng.random() < 0.70:
        journey.append("Treatment")
    journey.append("Discharge")

    # Generate timestamps. Delays are deliberately exaggerated for analysis.
    current_time = arrival_time
    events: list[Event] = []
    for index, activity in enumerate(journey, start=1):
        if index > 1:
            current_time += timedelta(minutes=random_duration(journey[index - 2], rng))
            if rng.random() < delay_probability:
                current_time += timedelta(minutes=rng.randint(30, 180))

        events.append(
            Event(
                case_id=case_id,
                event_id=f"{case_id}-E{index:02d}",
                activity_name=activity,
                timestamp=current_time,
                department=choose_department(activity, rng),
                patient_category=category,
                doctor_id=doctor_id,
                event_status="Completed",
            )
        )

    return events


def generate_events(
    cases: int,
    seed: int,
    rework_probability: float,
    delay_probability: float,
    start_date: datetime,
) -> Iterable[Event]:
    """Yield events for each synthetic case in timestamp order within each case."""
    rng = random.Random(seed)

    for case_number in range(1, cases + 1):
        # Spread arrivals over several days, with more arrivals during daytime.
        day_offset = rng.randint(0, 6)
        hour = rng.choices(
            list(range(24)),
            weights=[
                1, 1, 1, 1, 1, 2, 4, 7, 9, 9, 8, 8,
                8, 8, 8, 8, 7, 7, 6, 5, 4, 3, 2, 1,
            ],
            k=1,
        )[0]
        minute = rng.randint(0, 59)
        arrival = start_date + timedelta(days=day_offset, hours=hour, minutes=minute)
        yield from build_journey(
            case_number=case_number,
            arrival_time=arrival,
            rng=rng,
            rework_probability=rework_probability,
            delay_probability=delay_probability,
        )


def write_csv(events: Iterable[Event], output_path: Path) -> int:
    """Write events to CSV and return the number of rows written."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "Case_ID",
        "Event_ID",
        "Activity_Name",
        "Timestamp",
        "Department",
        "Patient_Category",
        "Doctor_ID",
        "Activity_Status",
    ]

    count = 0
    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for event in events:
            writer.writerow(
                {
                    "Case_ID": event.case_id,
                    "Event_ID": event.event_id,
                    "Activity_Name": event.activity_name,
                    "Timestamp": event.timestamp.isoformat(timespec="seconds"),
                    "Department": event.department,
                    "Patient_Category": event.patient_category,
                    "Doctor_ID": event.doctor_id,
                    "Activity_Status": event.event_status,
                }
            )
            count += 1
    return count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate synthetic CareFlow hospital event logs."
    )
    parser.add_argument(
        "--cases", type=int, default=500,
        help="Number of synthetic patient journeys to generate (default: 500).",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducible output (default: 42).",
    )
    parser.add_argument(
        "--rework-probability", type=float, default=0.40,
        help="Probability of adding a repeated activity loop, from 0 to 1 (default: 0.40).",
    )
    parser.add_argument(
        "--delay-probability", type=float, default=0.20,
        help="Probability of adding an extra 30–180 minute delay between events (default: 0.20).",
    )
    parser.add_argument(
        "--start-date", default="2026-01-01T00:00:00",
        help="Start date/time in ISO format (default: 2026-01-01T00:00:00).",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("data/synthetic_event_logs.csv"),
        help="Output CSV path (default: data/synthetic_event_logs.csv).",
    )
    args = parser.parse_args()

    if args.cases < 1:
        parser.error("--cases must be at least 1.")
    for name in ("rework_probability", "delay_probability"):
        value = getattr(args, name)
        if not 0.0 <= value <= 1.0:
            parser.error(f"--{name.replace('_', '-')} must be between 0 and 1.")
    try:
        args.start_date = datetime.fromisoformat(args.start_date)
    except ValueError:
        parser.error("--start-date must be a valid ISO date/time, e.g. 2026-01-01T00:00:00.")

    return args


def main() -> None:
    args = parse_args()
    row_count = write_csv(
        generate_events(
            cases=args.cases,
            seed=args.seed,
            rework_probability=args.rework_probability,
            delay_probability=args.delay_probability,
            start_date=args.start_date,
        ),
        args.output,
    )
    print(f"Generated {row_count:,} synthetic events across {args.cases:,} cases.")
    print(f"Output: {args.output.resolve()}")
    print("Reminder: these are fictional development data, not clinical evidence.")


if __name__ == "__main__":
    main()
