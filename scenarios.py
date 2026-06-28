from __future__ import annotations

from copy import deepcopy
from typing import Any


SCENARIOS: dict[str, dict[str, Any]] = {
    "normal": {
        "key": "normal",
        "name": "Normalbetrieb",
        "description": "Moderate Auslastung an einem regulären Studientag.",
        "simulation_minutes": 480,
        "exam_days": 14,
        "opening_minutes_per_day": 480,
        "replications": 30,
        "sample_interval": 10,
        "arrivals_per_hour": 32,
        "mean_stay_minutes": 125,
        "max_wait_minutes": 25,
        "resources": {
            "study_seats": 80,
            "pc_workstations": 22,
            "group_rooms": 8,
        },
        "demand_probabilities": {
            "study_seats": 0.66,
            "pc_workstations": 0.22,
            "group_rooms": 0.12,
        },
        "reservation_enabled": False,
        "reservation_share": 0.0,
        "seed": 42,
    },
    "exam": {
        "key": "exam",
        "name": "Prüfungsphase",
        "description": "Höhere Ankunftsrate, längere Aufenthalte und mehr Gruppennachfrage.",
        "simulation_minutes": 480,
        "exam_days": 14,
        "opening_minutes_per_day": 480,
        "replications": 30,
        "sample_interval": 10,
        "arrivals_per_hour": 54,
        "mean_stay_minutes": 170,
        "max_wait_minutes": 35,
        "resources": {
            "study_seats": 80,
            "pc_workstations": 22,
            "group_rooms": 8,
        },
        "demand_probabilities": {
            "study_seats": 0.55,
            "pc_workstations": 0.25,
            "group_rooms": 0.20,
        },
        "reservation_enabled": False,
        "reservation_share": 0.0,
        "seed": 42,
    },
    "reservation": {
        "key": "reservation",
        "name": "Prüfungsphase mit Reservierungssystem",
        "description": "Prüfungsphase mit Priorität für reservierte Gruppenräume.",
        "simulation_minutes": 480,
        "exam_days": 14,
        "opening_minutes_per_day": 480,
        "replications": 30,
        "sample_interval": 10,
        "arrivals_per_hour": 54,
        "mean_stay_minutes": 170,
        "max_wait_minutes": 35,
        "resources": {
            "study_seats": 80,
            "pc_workstations": 22,
            "group_rooms": 8,
        },
        "demand_probabilities": {
            "study_seats": 0.55,
            "pc_workstations": 0.25,
            "group_rooms": 0.20,
        },
        "reservation_enabled": True,
        "reservation_share": 0.55,
        "seed": 42,
    },
}


def get_scenario(key: str) -> dict[str, Any]:
    if key not in SCENARIOS:
        valid = ", ".join(SCENARIOS)
        raise ValueError(f"Unbekanntes Szenario '{key}'. Gültig sind: {valid}.")
    return deepcopy(SCENARIOS[key])


def list_scenarios() -> list[dict[str, Any]]:
    scenarios: list[dict[str, Any]] = []
    for scenario in SCENARIOS.values():
        scenarios.append(
            {
                "key": scenario["key"],
                "name": scenario["name"],
                "description": scenario["description"],
                "defaults": {
                    "study_seats": scenario["resources"]["study_seats"],
                    "pc_workstations": scenario["resources"]["pc_workstations"],
                    "group_rooms": scenario["resources"]["group_rooms"],
                    "arrivals_per_hour": scenario["arrivals_per_hour"],
                    "mean_stay_minutes": scenario["mean_stay_minutes"],
                    "max_wait_minutes": scenario["max_wait_minutes"],
                    "exam_days": scenario["exam_days"],
                    "opening_minutes_per_day": scenario["opening_minutes_per_day"],
                    "replications": scenario["replications"],
                    "seed": scenario["seed"],
                },
            }
        )
    return scenarios
