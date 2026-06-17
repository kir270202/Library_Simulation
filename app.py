from __future__ import annotations

import math
import os
from typing import Any

from flask import Flask, jsonify, render_template, request

from scenarios import get_scenario, list_scenarios
from simulation import run_simulation


app = Flask(__name__)


def _number(
    payload: dict[str, Any],
    key: str,
    default: float,
    minimum: float,
    *,
    exclusive_minimum: bool = False,
) -> float:
    value = payload.get(key, default)
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Parameter '{key}' muss eine Zahl sein.") from exc
    if not math.isfinite(number):
        raise ValueError(f"Parameter '{key}' muss eine endliche Zahl sein.")
    if exclusive_minimum and number <= minimum:
        raise ValueError(f"Parameter '{key}' muss groesser als {minimum:g} sein.")
    if not exclusive_minimum and number < minimum:
        raise ValueError(f"Parameter '{key}' muss mindestens {minimum:g} sein.")
    return number


def _integer(payload: dict[str, Any], key: str, default: int, minimum: int) -> int:
    number = _number(payload, key, default, minimum)
    if not number.is_integer():
        raise ValueError(f"Parameter '{key}' muss eine ganze Zahl sein.")
    return int(number)


def _optional_seed(payload: dict[str, Any], default: int | None) -> int | None:
    seed = payload.get("seed", default)
    if isinstance(seed, str):
        seed = seed.strip()
    if seed in ("", None):
        return None

    try:
        number = _number({"seed": seed}, "seed", 0, 0)
    except ValueError as exc:
        raise ValueError(
            "Parameter 'seed' muss leer oder eine nicht-negative ganze Zahl sein."
        ) from exc
    if not number.is_integer():
        raise ValueError(
            "Parameter 'seed' muss leer oder eine nicht-negative ganze Zahl sein."
        )
    return int(number)


def _build_config(payload: dict[str, Any]) -> dict[str, Any]:
    scenario_key = str(payload.get("scenario", "normal"))
    config = get_scenario(scenario_key)

    config["resources"] = {
        "study_seats": _integer(
            payload, "study_seats", config["resources"]["study_seats"], 0
        ),
        "pc_workstations": _integer(
            payload, "pc_workstations", config["resources"]["pc_workstations"], 0
        ),
        "group_rooms": _integer(
            payload, "group_rooms", config["resources"]["group_rooms"], 0
        ),
    }
    config["arrivals_per_hour"] = _number(
        payload, "arrivals_per_hour", config["arrivals_per_hour"], 0
    )
    config["mean_stay_minutes"] = _number(
        payload,
        "mean_stay_minutes",
        config["mean_stay_minutes"],
        0,
        exclusive_minimum=True,
    )
    config["max_wait_minutes"] = _number(
        payload, "max_wait_minutes", config["max_wait_minutes"], 0
    )

    config["seed"] = _optional_seed(payload, config.get("seed"))

    return config


@app.get("/")
def index() -> str:
    return render_template("index.html", scenarios=list_scenarios())


@app.post("/simulate")
def simulate():
    payload = request.get_json(silent=True) or {}
    try:
        config = _build_config(payload)
        result = run_simulation(config)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(result)


if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)
