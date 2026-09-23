"""Deterministic synthetic data generator.

    python -m app.data.generate            # writes app/data/generated/*.csv

Same SEED -> byte-identical CSVs. The CSVs are the single source for both backends:
DuckDB loads them at startup, scripts/load_bigquery.py loads them into BigQuery.
"""
from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

from app.config import DATA_DIR
from app.data.catalog import MACHINES, SENSORS
from app.data.scenarios import DATA_END, DATA_START, SCENARIO_DATE, SCENARIOS

SEED = 20261008

SENSOR_COLUMNS = ["row_id", "scenario_id", "ts", "line", "machine", "sensor", "value", "unit"]
EVENT_COLUMNS = ["row_id", "scenario_id", "ts", "line", "machine", "event_type", "code", "severity", "actor", "message"]
CATALOG_COLUMNS = ["row_id", "machine", "machine_name", "sensor", "unit", "normal_low", "normal_high", "sop_section"]


def to_dt(hhmm: str) -> datetime:
    fmt = "%Y-%m-%d %H:%M:%S" if hhmm.count(":") == 2 else "%Y-%m-%d %H:%M"
    return datetime.strptime(f"{SCENARIO_DATE} {hhmm}", fmt)


def _minutes(start: str, end: str):
    t, stop = to_dt(start), to_dt(end)
    while t <= stop:
        yield t
        t += timedelta(minutes=1)


def _apply_effects(sensor: str, t: datetime, base: float, effects: list[dict]) -> float | None:
    """Return the noiseless value at time t, or None if the sample is missing."""
    value = base
    for e in effects:
        if e["sensor"] != sensor:
            continue
        start = to_dt(e["start"])
        if e["type"] == "step" and t >= start:
            value = e["value"]
        elif e["type"] == "ramp" and t >= start:
            end = to_dt(e["end"])
            frac = min(1.0, (t - start).total_seconds() / max(1.0, (end - start).total_seconds()))
            value = base + (e["to"] - base) * frac
        elif e["type"] == "missing" and start <= t <= to_dt(e["end"]):
            return None
    return value


def generate_rows(scenario_id: str, spec: dict, rng: random.Random):
    line = spec["line"]
    sensors, events = [], []
    n = 0
    for t in _minutes(DATA_START, DATA_END):
        for sensor, s in SENSORS.items():
            v = _apply_effects(sensor, t, s["base"], spec["effects"])
            if v is None:
                continue
            noise = rng.gauss(0, s["noise"]) if s["noise"] else 0.0
            n += 1
            sensors.append(dict(
                row_id=f"{scenario_id}-S{n:05d}", scenario_id=scenario_id,
                ts=t.strftime("%Y-%m-%d %H:%M:%S"), line=line, machine=s["machine"], sensor=sensor,
                value=round(v + noise, 1), unit=s["unit"],
            ))
    # Routine background entries every scenario has, plus the story events.
    routine = [
        dict(ts="00:30:00", event_type="operator_note", machine="M4", code="QC", severity="info",
             actor="QC inspector", message="Hourly QC check passed."),
        dict(ts="01:30:00", event_type="operator_note", machine="M4", code="QC", severity="info",
             actor="QC inspector", message="Hourly QC check passed."),
    ]
    for i, e in enumerate(sorted(routine + spec["events"], key=lambda e: e["ts"]), start=1):
        events.append(dict(
            row_id=f"{scenario_id}-E{i:03d}", scenario_id=scenario_id,
            ts=to_dt(e["ts"]).strftime("%Y-%m-%d %H:%M:%S"), line=line, machine=e["machine"] or "",
            event_type=e["event_type"], code=e["code"], severity=e["severity"], actor=e["actor"],
            message=e["message"],
        ))
    return sensors, events


def catalog_rows():
    rows = []
    for i, (sensor, s) in enumerate(SENSORS.items(), start=1):
        rows.append(dict(row_id=f"CAT-{i:02d}", machine=s["machine"], machine_name=MACHINES[s["machine"]],
                         sensor=sensor, unit=s["unit"], normal_low=s["normal_low"],
                         normal_high=s["normal_high"], sop_section=s["sop"]))
    return rows


def _write(path: Path, columns: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def generate(out_dir: Path = DATA_DIR, seed: int = SEED) -> dict[str, int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    all_sensors, all_events = [], []
    for sid in sorted(SCENARIOS):
        rng = random.Random(f"{seed}-{sid}")  # per-scenario stream: editing one scenario leaves others unchanged
        s, e = generate_rows(sid, SCENARIOS[sid], rng)
        all_sensors += s
        all_events += e
    catalog = catalog_rows()
    _write(out_dir / "sensor_readings.csv", SENSOR_COLUMNS, all_sensors)
    _write(out_dir / "events.csv", EVENT_COLUMNS, all_events)
    _write(out_dir / "sensor_catalog.csv", CATALOG_COLUMNS, catalog)
    return {"sensor_readings": len(all_sensors), "events": len(all_events), "sensor_catalog": len(catalog)}


def ensure_generated(out_dir: Path = DATA_DIR) -> None:
    if not all((out_dir / f"{t}.csv").exists() for t in ("sensor_readings", "events", "sensor_catalog")):
        generate(out_dir)


if __name__ == "__main__":
    counts = generate()
    print(f"Wrote {DATA_DIR}: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
