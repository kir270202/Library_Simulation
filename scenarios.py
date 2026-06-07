from __future__ import annotations

from copy import deepcopy
from typing import Any


SCENARIOS: dict[str, dict[str, Any]] = {
    "normal": {
        "key": "normal",
        "name": "Normalbetrieb",
        "description": "Moderate Auslastung an einem regulaeren Studientag.",
        "simulation_minutes": 480,
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
        "name": "Pruefungsphase",
        "description": "Hoehere Ankunftsrate, laengere Aufenthalte und mehr Gruppennachfrage.",
        "simulation_minutes": 480,
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
        "name": "Pruefungsphase mit Reservierungssystem",
        "description": "Examensphase mit Prioritaet fuer reservierte Gruppenraeume.",
        "simulation_minutes": 480,
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
        raise ValueError(f"Unbekanntes Szenario '{key}'. Gueltig sind: {valid}.")
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
                    "seed": scenario["seed"],
                },
            }
        )
    return scenarios
