const scenarios = JSON.parse(document.getElementById("scenario-data").textContent);
const scenarioByKey = Object.fromEntries(scenarios.map((scenario) => [scenario.key, scenario]));

const resourceOrder = ["study_seats", "pc_workstations", "group_rooms"];
const resourceLabels = {
    study_seats: "Lernplätze",
    pc_workstations: "PC-Plätze",
    group_rooms: "Gruppenräume",
};
const chartColors = {
    study_seats: "#2f6fbd",
    pc_workstations: "#f0a202",
    group_rooms: "#e4572e",
    rejected: "#d7263d",
    served: "#2f6fbd",
    arrivals: "#222222",
};

const form = document.getElementById("simulation-form");
const scenarioSelect = document.getElementById("scenario");
const scenarioDescription = document.getElementById("scenario-description");
const statusMessage = document.getElementById("status-message");
const simulateButton = document.getElementById("simulate-button");
const interpretationSection = document.getElementById("interpretation-section");
const interpretationList = document.getElementById("interpretation-list");
const interpretationHeadline = document.getElementById("interpretation-headline");
const resultConfigLine = document.getElementById("result-config-line");
const resourceTableSection = document.getElementById("resource-table-section");
const dailyTableSection = document.getElementById("daily-table-section");
const liveProgress = document.getElementById("live-progress");

const charts = {};
let hasCompletedSimulation = false;
let isApplyingScenarioDefaults = false;
let progressTimer = null;

if (window.Chart) {
    Chart.defaults.color = "#111111";
    Chart.defaults.borderColor = "#8f8f8f";
    Chart.defaults.font.family = '"Courier New", Courier, monospace';
    Chart.defaults.font.size = 13;
    Chart.defaults.font.weight = "700";
}

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

    isApplyingScenarioDefaults = true;
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
    setValue("exam_days", defaults.exam_days);
    setValue("opening_minutes_per_day", defaults.opening_minutes_per_day);
    setValue("replications", defaults.replications);
    setValue("seed", defaults.seed);
    isApplyingScenarioDefaults = false;
}

function payloadFromForm() {
    return {
        scenario: scenarioSelect.value,
        study_seats: field("study_seats").value,
        pc_workstations: field("pc_workstations").value,
        group_rooms: field("group_rooms").value,
        arrivals_per_hour: field("arrivals_per_hour").value,
        mean_stay_minutes: field("mean_stay_minutes").value,
        max_wait_minutes: field("max_wait_minutes").value,
        exam_days: field("exam_days").value,
        opening_minutes_per_day: field("opening_minutes_per_day").value,
        replications: field("replications").value,
        seed: field("seed").value,
    };
}

function setStatus(type, message) {
    statusMessage.className = `status-message status-${type}`;
    statusMessage.textContent = message;
}

function markResultsStale() {
    if (!hasCompletedSimulation || isApplyingScenarioDefaults) {
        return;
    }
    setStatus("warning", "Einstellungen geändert – Simulation erneut starten, um die Ergebnisse zu aktualisieren.");
    resultConfigLine.classList.add("is-stale");
}

function setLoading(isLoading) {
    simulateButton.disabled = isLoading;
    simulateButton.classList.toggle("is-loading", isLoading);
    form.setAttribute("aria-busy", isLoading ? "true" : "false");
}

function startLiveProgress(payload) {
    const examDays = Math.max(Number(payload.exam_days) || 1, 1);
    const replications = Math.max(Number(payload.replications) || 1, 1);
    const openingMinutes = Math.max(Number(payload.opening_minutes_per_day) || 60, 1);
    const totalMinutes = examDays * replications * openingMinutes;
    const estimatedMs = Math.min(Math.max(totalMinutes / 70, 1200), 8000);
    const startedAt = performance.now();

    liveProgress.hidden = false;
    if (progressTimer) {
        clearInterval(progressTimer);
    }

    const update = () => {
        const elapsed = performance.now() - startedAt;
        const progress = Math.min(elapsed / estimatedMs, 0.985);
        const completedMinutes = Math.floor(progress * totalMinutes);
        const currentReplication = Math.min(
            Math.floor(completedMinutes / (examDays * openingMinutes)) + 1,
            replications,
        );
        const withinReplication = completedMinutes % (examDays * openingMinutes);
        const currentDay = Math.min(Math.floor(withinReplication / openingMinutes) + 1, examDays);
        const currentMinute = Math.min(withinReplication % openingMinutes, openingMinutes);

        field("live-replication").textContent = `${currentReplication}/${replications}`;
        field("live-day").textContent = `${currentDay}/${examDays}`;
        field("live-minute").textContent = `${currentMinute}/${openingMinutes}`;
        field("live-elapsed").textContent = `${(elapsed / 1000).toFixed(1)} s`;
    };

    update();
    progressTimer = setInterval(update, 100);
}

function stopLiveProgress(result) {
    if (progressTimer) {
        clearInterval(progressTimer);
        progressTimer = null;
    }
    if (result) {
        field("live-replication").textContent = `${result.summary.replications}/${result.summary.replications}`;
        field("live-day").textContent = `${result.summary.exam_days}/${result.summary.exam_days}`;
        field("live-minute").textContent = `${formatNumber(result.summary.opening_minutes_per_day)}/${formatNumber(result.summary.opening_minutes_per_day)}`;
    }
}

function formatPercent(value) {
    return `${Number(value).toFixed(2)}%`;
}

function formatNumber(value) {
    const number = Number(value);
    if (Number.isInteger(number)) {
        return String(number);
    }
    return number.toFixed(2);
}

function updateSummary(summary) {
    field("metric-exam-days").textContent = summary.exam_days;
    field("metric-replications").textContent = summary.replications;
    field("metric-arrivals").textContent = formatNumber(summary.total_arrivals);
    field("metric-served").textContent = formatNumber(summary.total_served);
    field("metric-rejected").textContent = formatNumber(summary.total_rejected);
    field("metric-rejection-rate").textContent = formatPercent(summary.rejection_rate);
    field("metric-waiting-time").textContent = `${formatNumber(summary.average_waiting_time)} min`;
    field("metric-busiest-day").textContent = `Tag ${summary.busiest_day}`;
    field("summary-note").textContent = summary.totals_meaning || "Summen beschreiben eine durchschnittliche vollständige Prüfungsphase.";
}

function findBottleneck(resources) {
    return resourceOrder
        .map((key) => ({ key, ...resources[key] }))
        .sort((a, b) => (
            b.rejected - a.rejected ||
            b.max_queue_length - a.max_queue_length ||
            b.utilization - a.utilization
        ))[0];
}

function updateResultConfigLine(result) {
    const config = result.config || {};
    const seedText = config.seed === null || config.seed === undefined || config.seed === ""
        ? "ohne Seed"
        : `Seed ${config.seed}`;
    resultConfigLine.textContent = `Ergebnis für: ${config.exam_days} Prüfungstage, ${config.replications} Wiederholungen, ${seedText}`;
    resultConfigLine.classList.remove("is-stale");
}

function updateTable(resources) {
    const tbody = field("resource-table-body");
    tbody.innerHTML = "";

    resourceOrder.forEach((key) => {
        const resource = resources[key];
        const row = document.createElement("tr");
        [
            resourceLabels[key],
            formatNumber(resource.served),
            formatNumber(resource.rejected),
            `${Number(resource.avg_waiting_time).toFixed(2)} min`,
            formatPercent(resource.utilization),
            formatNumber(resource.max_queue_length),
        ].forEach((value) => {
            const cell = document.createElement("td");
            cell.textContent = value;
            row.appendChild(cell);
        });
        tbody.appendChild(row);
    });
    resourceTableSection.hidden = false;
}

function updateDailyTable(dailyResults) {
    const tbody = field("daily-table-body");
    tbody.innerHTML = "";

    dailyResults.forEach((day) => {
        const row = document.createElement("tr");
        [
            day.day,
            formatNumber(day.arrivals),
            formatNumber(day.served),
            formatNumber(day.rejected),
            formatPercent(day.rejection_rate),
            `${Number(day.average_waiting_time).toFixed(2)} min`,
            formatNumber(day.maximum_queue_length),
        ].forEach((value) => {
            const cell = document.createElement("td");
            cell.textContent = value;
            row.appendChild(cell);
        });
        tbody.appendChild(row);
    });
    dailyTableSection.hidden = false;
}

function updateInterpretation(interpretation) {
    interpretationList.innerHTML = "";

    if (!interpretation || interpretation.length === 0) {
        interpretationSection.hidden = true;
        return;
    }

    interpretationHeadline.textContent = field("metric-bottleneck").textContent === "-"
        ? ""
        : `Wahrscheinlicher Hauptengpass: ${field("metric-bottleneck").textContent}`;

    interpretation.forEach((text) => {
        const item = document.createElement("li");
        item.textContent = text;
        interpretationList.appendChild(item);
    });
    interpretationSection.hidden = false;
}

function chartDataset(label, data, color) {
    return {
        label,
        data,
        borderColor: color,
        backgroundColor: color,
        tension: 0,
        borderWidth: 2,
        pointRadius: 0,
    };
}

function replaceChart(key, canvasId, config) {
    if (charts[key]) {
        charts[key].destroy();
    }
    config.options = {
        ...config.options,
        plugins: {
            ...(config.options?.plugins || {}),
            legend: {
                labels: {
                    boxWidth: 14,
                    padding: 12,
                    color: "#050505",
                    font: { size: 13, weight: "700" },
                },
                ...(config.options?.plugins?.legend || {}),
            },
        },
        scales: {
            ...(config.options?.scales || {}),
            x: {
                ...(config.options?.scales?.x || {}),
                ticks: {
                    color: "#050505",
                    font: { size: 12, weight: "700" },
                    ...(config.options?.scales?.x?.ticks || {}),
                },
                title: {
                    color: "#050505",
                    font: { size: 13, weight: "700" },
                    ...(config.options?.scales?.x?.title || {}),
                },
                grid: {
                    color: "#b0b0b0",
                    ...(config.options?.scales?.x?.grid || {}),
                },
            },
            y: {
                ...(config.options?.scales?.y || {}),
                ticks: {
                    color: "#050505",
                    font: { size: 12, weight: "700" },
                    ...(config.options?.scales?.y?.ticks || {}),
                },
                title: {
                    color: "#050505",
                    font: { size: 13, weight: "700" },
                    ...(config.options?.scales?.y?.title || {}),
                },
                grid: {
                    color: "#a8a8a8",
                    ...(config.options?.scales?.y?.grid || {}),
                },
            },
        },
    };
    charts[key] = new Chart(document.getElementById(canvasId), config);
}

function resizeCharts() {
    Object.values(charts).forEach((chart) => chart.resize());
}

function updateCharts(result) {
    const labels = resourceOrder.map((key) => resourceLabels[key]);
    const utilization = resourceOrder.map((key) => result.resources[key].utilization);
    const rejected = resourceOrder.map((key) => result.resources[key].rejected);
    const timeline = result.average_daily_timeline || result.timeline;
    const timelineLabels = timeline.map((row) => row.time);
    const dailyLabels = result.daily_results.map((row) => `Tag ${row.day}`);

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
                timeline.map((row) => row[`${key}_occupied`]),
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
                timeline.map((row) => row[`${key}_queue`]),
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

    replaceChart("dailyRequests", "daily-requests-chart", {
        type: "bar",
        data: {
            labels: dailyLabels,
            datasets: [
                {
                    label: "Ankünfte",
                    data: result.daily_results.map((row) => row.arrivals),
                    backgroundColor: chartColors.arrivals,
                },
                {
                    label: "Bedient",
                    data: result.daily_results.map((row) => row.served),
                    backgroundColor: chartColors.served,
                },
                {
                    label: "Abgewiesen",
                    data: result.daily_results.map((row) => row.rejected),
                    backgroundColor: chartColors.rejected,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: { boxWidth: 10, padding: 10 },
                },
            },
            scales: { y: { beginAtZero: true } },
        },
    });

    replaceChart("dailyRejection", "daily-rejection-chart", {
        type: "line",
        data: {
            labels: dailyLabels,
            datasets: [chartDataset(
                "Ablehnungsrate in Prozent",
                result.daily_results.map((row) => row.rejection_rate),
                chartColors.rejected,
            )],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } },
        },
    });

    replaceChart("dailyWaiting", "daily-waiting-chart", {
        type: "line",
        data: {
            labels: dailyLabels,
            datasets: [chartDataset(
                "Mittlere Wartezeit in Minuten",
                result.daily_results.map((row) => row.average_waiting_time),
                chartColors.served,
            )],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } },
        },
    });
}

async function runSimulation() {
    setStatus("running", "Prüfungsphase wird simuliert … bitte warten.");
    setLoading(true);
    const payload = payloadFromForm();
    startLiveProgress(payload);

    try {
        const response = await fetch("/simulate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Die Simulation konnte nicht gestartet werden.");
        }

        updateSummary(result.summary);
        const bottleneck = findBottleneck(result.resources);
        field("metric-bottleneck").textContent = bottleneck ? resourceLabels[bottleneck.key] : "-";
        updateResultConfigLine(result);
        updateTable(result.resources);
        updateDailyTable(result.daily_results);
        updateCharts(result);
        updateInterpretation(result.interpretation);
        stopLiveProgress(result);
        hasCompletedSimulation = true;
        setStatus("success", "Simulation abgeschlossen.");
    } catch (error) {
        stopLiveProgress();
        const detail = error.message ? ` ${error.message}` : "";
        setStatus("error", `Fehler bei der Simulation. Bitte Parameter prüfen.${detail}`);
    } finally {
        setLoading(false);
    }
}

bindRange("arrivals_per_hour", "arrivals_per_hour_range");
bindRange("mean_stay_minutes", "mean_stay_minutes_range");
bindRange("max_wait_minutes", "max_wait_minutes_range");

scenarioSelect.addEventListener("change", () => {
    applyScenarioDefaults();
    markResultsStale();
});

form.addEventListener("input", markResultsStale);
form.addEventListener("change", markResultsStale);

form.addEventListener("submit", (event) => {
    event.preventDefault();
    runSimulation();
});

document.querySelectorAll("details").forEach((details) => {
    details.addEventListener("toggle", () => {
        if (details.open) {
            requestAnimationFrame(resizeCharts);
        }
    });
});

applyScenarioDefaults();
runSimulation();
