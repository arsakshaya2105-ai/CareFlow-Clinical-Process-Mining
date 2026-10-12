#!/usr/bin/env python3
"""Generate fictional hospital activity records for the CareFlow project.

Run from the repository root:
    python src/generate_event_logs.py
    python src/generate_event_logs.py --cases 1000 --seed 7

All records are synthetic and are intended for development and testing only.
"""

import argparse
import csv
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

# Illustrative time gaps after each activity, in minutes. These are not
# clinical standards and should not be interpreted as real hospital data.
ACTIVITY_GAPS = {
    "Registration": (2, 10),
    "Triage": (3, 20),
    "Doctor Consultation": (5, 45),
    "Laboratory Test": (10, 75),
    "X-Ray": (10, 60),
    "Treatment": (5, 90),
    "Discharge": (3, 25),
}

PATIENT_GROUPS = ["Low Acuity", "Moderate Acuity", "High Acuity"]
DEPARTMENTS = {"X-Ray": "Radiology", "Laboratory Test": "Laboratory"}
ARRIVAL_WEIGHTS = [1, 1, 1, 1, 1, 2, 4, 7, 9, 9, 8, 8, 8, 8, 8, 8, 7, 7, 6, 5, 4, 3, 2, 1]


@dataclass(frozen=True)
class HospitalEvent:
    """One activity recorded during a fictional patient journey."""

    case_id: str
    event_id: str
    activity: str
    timestamp: datetime
    department: str
    patient_category: str
    doctor_id: str
    status: str = "Completed"


def pick_arrival(start: datetime, rng: random.Random) -> datetime:
    """Choose an arrival during a seven-day sample period."""
    day = rng.randint(0, 6)
    hour = rng.choices(range(24), weights=ARRIVAL_WEIGHTS, k=1)[0]
    return start + timedelta(days=day, hours=hour, minutes=rng.randint(0, 59))


def build_activity_list(rng: random.Random, rework_chance: float) -> list[str]:
    """Create a pathway with optional tests and a possible repeated activity."""
    activities = ["Registration", "Triage", "Doctor Consultation"]
    diagnostic_path = rng.choices(
        ["none", "lab", "xray", "both"], weights=[20, 30, 25, 25], k=1
    )[0]

    if diagnostic_path == "lab":
        activities.extend(["Laboratory Test", "Doctor Consultation"])
    elif diagnostic_path == "xray":
        activities.extend(["X-Ray", "Doctor Consultation"])
    elif diagnostic_path == "both":
        tests = ["Laboratory Test", "X-Ray"]
        rng.shuffle(tests)
        activities.extend(tests)
        activities.append("Doctor Consultation")

    if rng.random() < rework_chance:
        repeated = rng.choice(["Triage", "Doctor Consultation"])
        activities.insert(max(2, len(activities) - 1), repeated)

    if rng.random() < 0.70:
        activities.append("Treatment")
    activities.append("Discharge")
    return activities


def create_case(
    case_number: int,
    arrival: datetime,
    rng: random.Random,
    rework_chance: float,
    delay_chance: float,
) -> list[HospitalEvent]:
    """Create the ordered events for one patient case."""
    case_id = f"P{case_number:05d}"
    category = rng.choices(PATIENT_GROUPS, weights=[50, 35, 15], k=1)[0]
    doctor_id = f"D{rng.randint(1, 12):03d}"
    activities = build_activity_list(rng, rework_chance)
    events = []
