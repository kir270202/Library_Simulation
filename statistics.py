from __future__ import annotations

from typing import Any


RESOURCE_KEYS = ("study_seats", "pc_workstations", "group_rooms")

RESOURCE_LABELS = {
    "study_seats": "Einzelarbeitsplätze",
    "pc_workstations": "PC-Arbeitsplätze",
    "group_rooms": "Gruppenräume",
}


def create_metric_buckets() -> dict[str, dict[str, Any]]:
    return {
        key: {
            "served": 0,
            "rejected": 0,
            "waiting_times": [],
            "usage_minutes": 0.0,
            "max_queue_length": 0,
            "arrived_people": 0,
            "served_people": 0,
            "rejected_people": 0,
        }
        for key in RESOURCE_KEYS
    }


def finalize_results(
    metrics: dict[str, dict[str, Any]],
    capacities: dict[str, int],
    simulation_minutes: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    resources: dict[str, Any] = {}
    total_arrivals = 0
    total_served = 0
    total_rejected = 0
    total_people = 0

    for key in RESOURCE_KEYS:
        bucket = metrics[key]
        served = int(bucket["served"])
        rejected = int(bucket["rejected"])
        total_arrivals += served + rejected
        total_served += served
        total_rejected += rejected
        total_people += int(bucket["arrived_people"])

        waiting_times = bucket["waiting_times"]
        avg_wait = sum(waiting_times) / len(waiting_times) if waiting_times else 0.0
        capacity = capacities.get(key, 0)
        if capacity > 0 and simulation_minutes > 0:
            utilization = bucket["usage_minutes"] / (capacity * simulation_minutes) * 100
        else:
            utilization = 0.0

        resources[key] = {
            "label": RESOURCE_LABELS[key],
            "served": served,
            "rejected": rejected,
            "rejection_rate": round((rejected / (served + rejected) * 100) if served + rejected else 0.0, 2),
            "avg_waiting_time": round(avg_wait, 2),
            "utilization": round(min(utilization, 100.0), 2),
            "max_queue_length": int(bucket["max_queue_length"]),
            "arrived_people": int(bucket["arrived_people"]),
            "served_people": int(bucket["served_people"]),
            "rejected_people": int(bucket["rejected_people"]),
            "waiting_time_total": round(float(sum(waiting_times)), 6),
            "waiting_count": int(len(waiting_times)),
        }

    rejection_rate = (total_rejected / total_arrivals * 100) if total_arrivals else 0.0
    all_waiting_times = [
        waiting_time
        for key in RESOURCE_KEYS
        for waiting_time in metrics[key]["waiting_times"]
    ]
    waiting_time_total = float(sum(all_waiting_times))
    waiting_count = len(all_waiting_times)
    summary = {
        "total_arrivals": total_arrivals,
        "total_served": total_served,
        "total_rejected": total_rejected,
        "rejection_rate": round(rejection_rate, 2),
        "average_waiting_time": round(
            waiting_time_total / waiting_count if waiting_count else 0.0, 2
        ),
        "total_people": total_people,
        "waiting_time_total": round(waiting_time_total, 6),
        "waiting_count": waiting_count,
    }

    return summary, resources


def build_interpretation(
    summary: dict[str, Any],
    resources: dict[str, Any],
    config: dict[str, Any],
    daily_results: list[dict[str, Any]] | None = None,
) -> list[str]:
    """Create a short, human-readable interpretation for the current model run."""
    if summary["total_arrivals"] == 0:
        return [
            "In der simulierten Prüfungsphase gab es keine Ankünfte. Für aussagekräftige Ergebnisse sollte die Ankunftsrate erhöht werden.",
        ]

    bottleneck_key = max(
        RESOURCE_KEYS,
        key=lambda key: (
            resources[key]["rejected"],
            resources[key]["max_queue_length"],
            resources[key]["utilization"],
        ),
    )
    bottleneck = resources[bottleneck_key]
    rejection_rate = float(summary["rejection_rate"])
    average_waiting_time = float(summary.get("average_waiting_time", 0.0))
    busiest_day = int(summary.get("busiest_day", 0))
    busiest_day_arrivals = float(summary.get("busiest_day_arrivals", 0.0))
    exam_days = int(summary.get("exam_days", 1))
    replications = int(summary.get("replications", 1))
    interpretation: list[str] = []

    if (
        bottleneck["rejected"] > 0
        or bottleneck["max_queue_length"] > 0
        or bottleneck["utilization"] >= 85
    ):
        interpretation.append(
            "Auf Basis der gewählten Modellannahmen ist der Hauptengpass wahrscheinlich "
            f"{bottleneck['label']}: durchschnittlich {bottleneck['rejected']:.2f} Abweisungen pro Prüfungsphase, "
            f"mittlere maximale Warteschlange {bottleneck['max_queue_length']:.2f} und "
            f"{bottleneck['utilization']:.2f}% Auslastung."
        )
    else:
        interpretation.append(
            "Auf Basis der gewählten Modellannahmen entsteht kein deutlicher Engpass; die Ressourcen wirken für diese Nachfrage ausreichend."
        )

    if busiest_day > 0:
        interpretation.append(
            f"Der stärkste Prüfungstag ist im Mittel Tag {busiest_day} mit {busiest_day_arrivals:.2f} Ankünften."
        )
    elif daily_results:
        busiest = max(daily_results, key=lambda row: row["arrivals"])
        interpretation.append(
            f"Der stärkste Prüfungstag ist im Mittel Tag {busiest['day']} mit {busiest['arrivals']:.2f} Ankünften."
        )

    if rejection_rate >= 20:
        interpretation.append(
            f"Die mittlere Ablehnungsrate der Prüfungsphase ist mit {rejection_rate:.2f}% hoch und deutet auf spürbare Kapazitätsprobleme hin."
        )
    elif rejection_rate >= 5:
        interpretation.append(
            f"Die mittlere Ablehnungsrate der Prüfungsphase ist mit {rejection_rate:.2f}% moderat."
        )
    else:
        interpretation.append(
            f"Die mittlere Ablehnungsrate der Prüfungsphase ist mit {rejection_rate:.2f}% niedrig."
        )

    max_wait = float(config.get("max_wait_minutes", 0.0))
    if max_wait > 0 and average_waiting_time >= max_wait * 0.5:
        interpretation.append(
            f"Die mittlere Wartezeit von {average_waiting_time:.2f} Minuten ist problematisch, weil sie einen großen Teil der maximal akzeptierten Wartezeit nutzt."
        )
    elif average_waiting_time >= 10:
        interpretation.append(
            f"Die mittlere Wartezeit von {average_waiting_time:.2f} Minuten sollte beobachtet werden."
        )
    else:
        interpretation.append(
            f"Die mittlere Wartezeit von {average_waiting_time:.2f} Minuten wirkt in diesem Modell unkritisch."
        )

    if config.get("reservation_enabled"):
        interpretation.append(
            "Das Reservierungsszenario priorisiert reservierte Gruppenräume. Sein Effekt sollte durch Vergleich mit der Prüfungsphase ohne Reservierung bewertet werden; die Simulation beweist keine reale Wirkung."
        )
    elif resources["group_rooms"]["rejected"] > 0 or resources["group_rooms"]["max_queue_length"] > 0:
        interpretation.append(
            "Bei Gruppenräumen könnte ein Reservierungssystem die Warteschlange anders verteilen; alternativ sollte zusätzliche Kapazität geprüft werden."
        )

    if bottleneck["utilization"] >= 90:
        interpretation.append(
            f"Eine naheliegende Verbesserung wäre zusätzliche oder flexiblere Kapazität bei {bottleneck['label']}, besonders für die {exam_days} getrennt simulierten Öffnungstage."
        )
    else:
        interpretation.append(
            f"Naheliegende Maßnahme: Kapazität und Nachfrageverteilung bei {bottleneck['label']} über weitere Annahmen oder reale Daten prüfen."
        )

    if replications > 1:
        interpretation.append(
            f"Die Kennzahlen sind Mittelwerte einer vollständigen Prüfungsphase über {replications} unabhängige Wiederholungen."
        )

    return interpretation
