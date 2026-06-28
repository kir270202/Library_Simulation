# Bibliotheks-/Lernraum-Simulation mit SimPy

Flask-Webanwendung für das Modul "Diskrete Simulation". Das Projekt simuliert eine Prüfungsphase in einer Hochschulbibliothek mit Einzelarbeitsplätzen, PC-Arbeitsplätzen und Gruppenräumen.

## Motivation

Vor Prüfungsphasen werden Lernplätze knapp. Die Simulation zeigt, wann Warteschlangen entstehen, welche Ressource zum Engpass wird und wie sich ein einfaches Reservierungssystem für Gruppenräume auswirken kann.

## Technologien

- Python
- Flask
- SimPy
- NumPy
- HTML/CSS/JavaScript
- Chart.js
- Docker

## Funktionen

- drei Szenarien: Normalbetrieb, Prüfungsphase, Prüfungsphase mit Reservierungssystem
- editierbare Kapazitäten, Öffnungstage, Öffnungsdauer und Simulationsparameter
- getrennte Simulation mehrerer Öffnungstage mit täglich leeren Ressourcen und Warteschlangen
- unabhängige Wiederholungen für stabilere Mittelwerte
- reproduzierbare Läufe über optionalen Random Seed
- sichtbarer Laufstatus beim Start der Simulation
- KPI-Karten, Ressourcen- und Tagestabellen, Diagramme und 95%-Konfidenzintervalle im JSON-Ergebnis
- kurze automatische Interpretation der Ergebnisse
- JSON-Endpunkt `POST /simulate`

## Lokaler Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Danach im Browser öffnen:

```text
http://127.0.0.1:5000
```

Unter Windows:

```bash
py -3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## Start mit Docker

```bash
docker compose up --build
```

Danach:

```text
http://127.0.0.1:5000
```

Container stoppen und entfernen:

```bash
docker compose down
```

## Projektstruktur

```text
library-room-simulation/
+-- app.py
+-- simulation.py
+-- scenarios.py
+-- statistics.py
+-- requirements.txt
+-- Dockerfile
+-- docker-compose.yml
+-- README.md
+-- docs/
|   +-- documentation.md
+-- templates/
|   +-- index.html
+-- static/
    +-- style.css
    +-- script.js
```

## Prüfungsphase, Wiederholungen und Seeds

Eine Prüfungsphase besteht aus mehreren getrennten Öffnungstagen. Für jeden Tag wird eine neue SimPy-Umgebung erstellt. Ressourcen, Warteschlangen, Studierende, Gruppen, Reservierungen und offene Anfragen werden nicht in den nächsten Tag übernommen. Das entspricht der Annahme, dass die Bibliothek zwischen zwei Öffnungstagen vollständig schließt.

Bei mehreren Wiederholungen wird die vollständige Prüfungsphase mehrfach unabhängig simuliert. Die angezeigten Summen sind deshalb Mittelwerte einer vollständigen Prüfungsphase, nicht die Summe aller Wiederholungen. Zusätzlich berechnet das Backend Mittelwert, Standardabweichung und ein 95%-Konfidenzintervall für Gesamtankünfte, Ablehnungsrate und mittlere Wartezeit.

Ein fester Random Seed reproduziert die komplette Prüfungsphase. Aus ihm werden deterministisch getrennte Zufallsströme für jede Wiederholung und jeden Tag abgeleitet. Bleibt der Seed leer, erzeugt jeder Start neue Zufallswerte.

## Kurze Interpretation der Ergebnisse

Eine hohe Auslastung bedeutet nicht automatisch ein gutes Ergebnis. Wenn Ressourcen fast dauerhaft belegt sind, entstehen schneller Warteschlangen und Ablehnungen. Wichtig sind deshalb Ablehnungsrate, durchschnittliche Wartezeit und maximale Warteschlangenlänge.

Das Reservierungssystem ist bewusst einfach modelliert: Reservierte Gruppen erhalten Priorität bei Gruppenräumen. Für eine Bewertung sollte das Szenario "Prüfungsphase" mit "Prüfungsphase mit Reservierungssystem" verglichen werden.

## Modellgrenzen

Die Parameter sind Modellannahmen und müssten in einer realen Untersuchung mit Beobachtungsdaten validiert werden. Das Modell enthält keine Datenbank, keinen Login, keine echten Reservierungsdaten und keine Tagesganglinie. Es bleibt absichtlich kompakt, damit Modell, Code und Ergebnisse nachvollziehbar sind.

## Screenshots

Für die finale Abgabe kann hier ein Screenshot der Weboberfläche ergänzt werden.

Weitere Details stehen in [docs/documentation.md](docs/documentation.md).
