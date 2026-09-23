"""Plant model: machines, sensors, normal ranges. Shared by generator, queries and UI copy.

Every line has the same four machines. Normal ranges are the SOP limits the agent
compares against (they are also loaded into the `sensor_catalog` table so the limit
numbers shown on evidence cards trace back to rows).
"""
from __future__ import annotations

MACHINES = {
    "M1": "M1 Feeder",
    "M2": "M2 Dryer",
    "M3": "M3 Molding",
    "M4": "M4 Inspection",
}

# sensor -> spec. base/noise drive the generator; normal_low/high are SOP limits.
SENSORS: dict[str, dict] = {
    "feed_rate_kgph":        dict(machine="M1", unit="kg/h",  base=120.0, noise=0.8,  normal_low=100.0, normal_high=135.0, sop="SOP 4.6", label="Feed rate"),
    "dryer_temp_c":          dict(machine="M2", unit="°C",    base=80.0,  noise=0.4,  normal_low=75.0,  normal_high=85.0,  sop="SOP 4.5", label="Dryer temperature"),
    "dew_point_c":           dict(machine="M2", unit="°C",    base=-40.0, noise=0.5,  normal_low=-50.0, normal_high=-30.0, sop="SOP 4.5", label="Resin dew point"),
    "mold_temp_c":           dict(machine="M3", unit="°C",    base=188.0, noise=0.6,  normal_low=180.0, normal_high=205.0, sop="SOP 4.2", label="Mold temperature"),
    "mold_temp_ref_c":       dict(machine="M3", unit="°C",    base=188.0, noise=0.6,  normal_low=180.0, normal_high=205.0, sop="SOP 4.7", label="Mold temperature (reference probe)"),
    "coolant_flow_lpm":      dict(machine="M3", unit="L/min", base=42.0,  noise=0.3,  normal_low=34.0,  normal_high=50.0,  sop="SOP 4.1", label="Coolant flow"),
    "coolant_inlet_temp_c":  dict(machine="M3", unit="°C",    base=18.0,  noise=0.2,  normal_low=12.0,  normal_high=24.0,  sop="SOP 4.1", label="Coolant inlet temperature"),
    "cv_position_pct":       dict(machine="M3", unit="%",     base=80.0,  noise=0.2,  normal_low=60.0,  normal_high=95.0,  sop="SOP 4.1", label="Cooling valve CV-{line} position"),
    "cv_command_pct":        dict(machine="M3", unit="%",     base=80.0,  noise=0.0,  normal_low=60.0,  normal_high=95.0,  sop="SOP 4.1", label="Cooling valve CV-{line} command"),
    "heater_power_pct":      dict(machine="M3", unit="%",     base=55.0,  noise=0.8,  normal_low=30.0,  normal_high=85.0,  sop="SOP 4.2", label="Heater power"),
    "hydraulic_pressure_bar": dict(machine="M3", unit="bar",  base=140.0, noise=0.7,  normal_low=125.0, normal_high=155.0, sop="SOP 4.4", label="Hydraulic pressure"),
    "reject_rate_pct":       dict(machine="M4", unit="%",     base=0.8,   noise=0.1,  normal_low=0.0,   normal_high=3.0,   sop="SOP 4.3", label="Reject rate"),
}

SENSOR_NAMES = list(SENSORS)


def sensor_label(sensor: str, line: int) -> str:
    return SENSORS[sensor]["label"].format(line=line)


# Known failure modes the agent may conclude. Used as an enum in submit_conclusion so
# the regression set can be graded exactly. "other" is allowed but never expected.
ROOT_CAUSE_KEYS = {
    "cv_valve_stuck_closed": "Cooling valve stuck (partly closed)",
    "cv_valve_stuck_open": "Cooling valve stuck open",
    "coolant_supply_temp_high": "Coolant supply (chiller) temperature too high",
    "coolant_filter_clogged": "Coolant filter / line clogged",
    "heater_stuck_on": "Mold heater stuck on",
    "temp_sensor_drift": "Mold temperature sensor drift",
    "setpoint_change": "Process setpoint changed",
    "hydraulic_pressure_low": "Hydraulic pressure low",
    "dryer_temp_low": "Resin dryer temperature low (wet resin)",
    "feeder_blockage": "Feeder blockage",
    "other": "Other (explain in text)",
}
