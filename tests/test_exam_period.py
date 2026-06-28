from __future__ import annotations

import json
import math
import unittest

from app import app
from scenarios import get_scenario
from simulation import run_exam_period


def base_config() -> dict:
    config = get_scenario("exam")
    config.update(
        {
            "exam_days": 2,
            "opening_minutes_per_day": 120,
            "simulation_minutes": 120,
            "replications": 2,
            "seed": 42,
        }
    )
    return config


def walk_numbers(value):
    if isinstance(value, dict):
        for child in value.values():
            yield from walk_numbers(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_numbers(child)
    elif isinstance(value, (int, float)):
        yield value


class ExamPeriodSimulationTest(unittest.TestCase):
    def test_one_examination_day_works(self):
        config = base_config()
        config["exam_days"] = 1
        result = run_exam_period(config)
        self.assertEqual(result["summary"]["exam_days"], 1)
        self.assertEqual(len(result["daily_results"]), 1)

    def test_fourteen_days_work(self):
        config = base_config()
        config["exam_days"] = 14
        config["opening_minutes_per_day"] = 60
        config["simulation_minutes"] = 60
        config["replications"] = 1
        result = run_exam_period(config)
        self.assertEqual(result["summary"]["exam_days"], 14)
        self.assertEqual(len(result["daily_results"]), 14)

    def test_same_seed_reproduces_result(self):
        config = base_config()
        self.assertEqual(run_exam_period(config), run_exam_period(config))

    def test_different_seed_can_produce_different_result(self):
        config_a = base_config()
        config_b = base_config()
        config_b["seed"] = 43
        self.assertNotEqual(
            run_exam_period(config_a)["summary"]["total_arrivals"],
            run_exam_period(config_b)["summary"]["total_arrivals"],
        )

    def test_resources_and_queues_reset_at_new_day_start(self):
        config = base_config()
        config["exam_days"] = 3
        result = run_exam_period(config)
        first_row = result["average_daily_timeline"][0]
        self.assertEqual(first_row["time"], 0)
        for key in ("study_seats", "pc_workstations", "group_rooms"):
            self.assertEqual(first_row[f"{key}_occupied"], 0)
            self.assertEqual(first_row[f"{key}_queue"], 0)

    def test_zero_resource_capacity_is_handled(self):
        config = base_config()
        config["resources"] = {
            "study_seats": 0,
            "pc_workstations": 0,
            "group_rooms": 0,
        }
        result = run_exam_period(config)
        self.assertGreaterEqual(result["summary"]["total_rejected"], 0)
        for resource in result["resources"].values():
            self.assertEqual(resource["utilization"], 0)

    def test_result_is_json_serializable(self):
        result = run_exam_period(base_config())
        json.dumps(result)

    def test_no_nan_or_infinity_is_returned(self):
        result = run_exam_period(base_config())
        for number in walk_numbers(result):
            self.assertTrue(math.isfinite(number))


class FlaskEndpointTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_invalid_exam_days_returns_400(self):
        response = self.client.post(
            "/simulate",
            json={
                "scenario": "exam",
                "exam_days": 0,
                "opening_minutes_per_day": 120,
                "replications": 1,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("exam_days", response.get_json()["error"])

    def test_invalid_replications_returns_400(self):
        response = self.client.post(
            "/simulate",
            json={
                "scenario": "exam",
                "exam_days": 1,
                "opening_minutes_per_day": 120,
                "replications": 101,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("replications", response.get_json()["error"])

    def test_valid_exam_period_request_returns_200(self):
        response = self.client.post(
            "/simulate",
            json={
                "scenario": "exam",
                "study_seats": 10,
                "pc_workstations": 5,
                "group_rooms": 2,
                "arrivals_per_hour": 12,
                "mean_stay_minutes": 45,
                "max_wait_minutes": 10,
                "exam_days": 2,
                "opening_minutes_per_day": 120,
                "replications": 2,
                "seed": 42,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["summary"]["exam_days"], 2)


if __name__ == "__main__":
    unittest.main()
