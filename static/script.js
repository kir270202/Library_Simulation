const scenarios = JSON.parse(document.getElementById("scenario-data").textContent);
const scenarioByKey = Object.fromEntries(scenarios.map((scenario) => [scenario.key, scenario]));

const resourceOrder = ["study_seats", "pc_workstations", "group_rooms"];
const resourceLabels = {
    study_seats: "Lernplätze",
    pc_workstations: "PC-Plätze",
    group_rooms: "Gruppenräume",
};
const chartColors = {
    study_seats: "#287c69",
    pc_workstations: "#6f5bb5",
    group_rooms: "#b97818",
    rejected: "#b7475b",
};

const form = document.getElementById("simulation-form");
const scenarioSelect = document.getElementById("scenario");
const scenarioDescription = document.getElementById("scenario-description");
const statusMessage = document.getElementById("status-message");
const simulateButton = document.getElementById("simulate-button");

const charts = {};

function field(id) {
    return document.getElementById(id);
}

function setValue(id, value) {
    field(id).value = value ?? "";
}

function bindRange(numberId, rangeId) {
    const numberInput = field(numberId);
    const rangeInput = field(rangeId);

    numberInput.addEventListener("input", () => {
        rangeInput.value = numberInput.value;
    });
    rangeInput.addEventListener("input", () => {
        numberInput.value = rangeInput.value;
    });
}

function applyScenarioDefaults() {
    const selected = scenarioByKey[scenarioSelect.value];
    if (!selected) {
        return;
    }

    scenarioDescription.textContent = selected.description;
    const defaults = selected.defaults;
    setValue("study_seats", defaults.study_seats);
    setValue("pc_workstations", defaults.pc_workstations);
    setValue("group_rooms", defaults.group_rooms);
    setValue("arrivals_per_hour", defaults.arrivals_per_hour);
    setValue("arrivals_per_hour_range", defaults.arrivals_per_hour);
    setValue("mean_stay_minutes", defaults.mean_stay_minutes);
    setValue("mean_stay_minutes_range", defaults.mean_stay_minutes);
    setValue("max_wait_minutes", defaults.max_wait_minutes);
    setValue("max_wait_minutes_range", defaults.max_wait_minutes);
    setValue("seed", defaults.seed);
}

function payloadFromForm() {
    return {
        scenario: scenarioSelect.value,
        study_seats: Number(field("study_seats").value),
        pc_workstations: Number(field("pc_workstations").value),
        group_rooms: Number(field("group_rooms").value),
        arrivals_per_hour: Number(field("arrivals_per_hour").value),
        mean_stay_minutes: Number(field("mean_stay_minutes").value),
        max_wait_minutes: Number(field("max_wait_minutes").value),
        seed: field("seed").value,
    };
}

function formatPercent(value) {
    return `${Number(value).toFixed(2)}%`;
}

function updateSummary(summary) {
    field("metric-arrivals").textContent = summary.total_arrivals;
    field("metric-served").textContent = summary.total_served;
    field("metric-rejected").textContent = summary.total_rejected;
    field("metric-rejection-rate").textContent = formatPercent(summary.rejection_rate);
}

function updateTable(resources) {
    const tbody = field("resource-table-body");
    tbody.innerHTML = "";

    resourceOrder.forEach((key) => {
        const resource = resources[key];
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${resourceLabels[key]}</td>
            <td>${resource.served}</td>
            <td>${resource.rejected}</td>
            <td>${resource.avg_waiting_time.toFixed(2)} min</td>
            <td>${formatPercent(resource.utilization)}</td>
            <td>${resource.max_queue_length}</td>
        `;
        tbody.appendChild(row);
    });
}

function chartDataset(label, data, color) {
    return {
        label,
        data,
        borderColor: color,
        backgroundColor: color,
        tension: 0.25,
        borderWidth: 2,
        pointRadius: 0,
    };
}

function replaceChart(key, canvasId, config) {
    if (charts[key]) {
        charts[key].destroy();
    }
    charts[key] = new Chart(document.getElementById(canvasId), config);
}

function updateCharts(result) {
    const labels = resourceOrder.map((key) => resourceLabels[key]);
    const utilization = resourceOrder.map((key) => result.resources[key].utilization);
    const rejected = resourceOrder.map((key) => result.resources[key].rejected);
    const timelineLabels = result.timeline.map((row) => row.time);

    replaceChart("utilization", "utilization-chart", {
        type: "bar",
        data: {
            labels,
            datasets: [{
                label: "Auslastung in Prozent",
                data: utilization,
                backgroundColor: resourceOrder.map((key) => chartColors[key]),
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, max: 100 } },
        },
    });

    replaceChart("rejected", "rejected-chart", {
        type: "bar",
        data: {
            labels,
            datasets: [{
                label: "Abgewiesene Nutzer/Gruppen",
                data: rejected,
                backgroundColor: chartColors.rejected,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
        },
    });

    replaceChart("occupancy", "occupancy-chart", {
        type: "line",
        data: {
            labels: timelineLabels,
            datasets: resourceOrder.map((key) => chartDataset(
                resourceLabels[key],
                result.timeline.map((row) => row[`${key}_occupied`]),
                chartColors[key],
            )),
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: {
                    position: "bottom",
                    labels: { boxWidth: 10, padding: 10 },
                },
            },
            scales: {
                x: { title: { display: true, text: "Minute" }, ticks: { maxTicksLimit: 6 } },
                y: { beginAtZero: true, ticks: { precision: 0 } },
            },
        },
    });

    replaceChart("queue", "queue-chart", {
        type: "line",
        data: {
            labels: timelineLabels,
            datasets: resourceOrder.map((key) => chartDataset(
                resourceLabels[key],
                result.timeline.map((row) => row[`${key}_queue`]),
                chartColors[key],
            )),
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: {
                    position: "bottom",
                    labels: { boxWidth: 10, padding: 10 },
                },
            },
            scales: {
                x: { title: { display: true, text: "Minute" }, ticks: { maxTicksLimit: 6 } },
                y: { beginAtZero: true, ticks: { precision: 0 } },
            },
        },
    });
}

async function runSimulation() {
    statusMessage.textContent = "Simulation läuft...";
    simulateButton.disabled = true;

    try {
        const response = await fetch("/simulate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payloadFromForm()),
        });
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Die Simulation konnte nicht gestartet werden.");
        }

        updateSummary(result.summary);
        updateTable(result.resources);
        updateCharts(result);
        statusMessage.textContent = "Ergebnisse aktualisiert.";
    } catch (error) {
        statusMessage.textContent = error.message;
    } finally {
        simulateButton.disabled = false;
    }
}

bindRange("arrivals_per_hour", "arrivals_per_hour_range");
bindRange("mean_stay_minutes", "mean_stay_minutes_range");
bindRange("max_wait_minutes", "max_wait_minutes_range");

scenarioSelect.addEventListener("change", () => {
    applyScenarioDefaults();
    runSimulation();
});

form.addEventListener("submit", (event) => {
    event.preventDefault();
    runSimulation();
});

applyScenarioDefaults();
runSimulation();
