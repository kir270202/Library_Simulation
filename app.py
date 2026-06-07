from __future__ import annotations

import os
from typing import Any

from flask import Flask, jsonify, render_template, request

from scenarios import get_scenario, list_scenarios
from simulation import run_simulation


app = Flask(__name__)


RESOURCE_KEYS = ("study_seats", "pc_workstations", "group_rooms")


def _number(payload: dict[str, Any], key: str, default: float, minimum: float) -> float:
    value = payload.get(key, default)
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Parameter '{key}' muss eine Zahl sein.") from exc
    if number < minimum:
        raise ValueError(f"Parameter '{key}' muss mindestens {minimum:g} sein.")
    return number


def _integer(payload: dict[str, Any], key: str, default: int, minimum: int) -> int:
    return int(round(_number(payload, key, default, minimum)))


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
        payload, "mean_stay_minutes", config["mean_stay_minutes"], 10
    )
    config["max_wait_minutes"] = _number(
        payload, "max_wait_minutes", config["max_wait_minutes"], 0
    )

    seed = payload.get("seed", config.get("seed"))
    if seed in ("", None):
        config["seed"] = None
    else:
        try:
            config["seed"] = int(seed)
        except (TypeError, ValueError) as exc:
            raise ValueError("Parameter 'seed' muss leer oder eine ganze Zahl sein.") from exc

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
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host=host, port=port, debug=debug)
