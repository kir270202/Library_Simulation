# Bibliotheks-/Lernraum-Simulation mit SimPy

Kleine Flask-Webanwendung für das Modul "Diskrete Simulation". Die App simuliert einen Studientag in einer Hochschulbibliothek mit Einzelarbeitsplätzen, PC-Arbeitsplätzen und Gruppenräumen. Die Simulation nutzt SimPy, zufällige Ankunftszeiten, Aufenthaltsdauern, Ressourcennachfrage und Gruppengrößen.

## Run without Docker

Requirements:

- Python 3.10 or newer
- `pip`

Create a virtual environment, install the dependencies, and start Flask:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

On Windows:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open the application in the browser:

```text
http://127.0.0.1:5000
```

Stop the app with `Ctrl+C` in the terminal.

## Run with Docker

Requirements:

- Docker
- Docker Compose, if you want to use the compose command

Start with Docker Compose:

```bash
docker compose up --build
```

Open the application in the browser:

```text
http://127.0.0.1:5000
```

Stop the app with `Ctrl+C`. To remove the stopped container network afterwards, run:

```bash
docker compose down
```

Alternative without Docker Compose:

```bash
docker build -t library-room-simulation .
docker run --rm -p 5000:5000 library-room-simulation
```

Open the application in the browser:

```text
http://127.0.0.1:5000
```

Inside Docker, Flask binds to `0.0.0.0` so that Docker port forwarding works. When started locally with `python app.py`, the app uses `127.0.0.1:5000` by default.

## Projektstruktur

```text
library-room-simulation/
+-- app.py
+-- simulation.py
+-- scenarios.py
+-- statistics.py
+-- Dockerfile
+-- docker-compose.yml
+-- requirements.txt
+-- README.md
+-- docs/
|   +-- documentation.md
+-- templates/
|   +-- index.html
+-- static/
    +-- style.css
    +-- script.js
```

## Szenarien

`Normalbetrieb`: moderate Ankunftsintensität, normale Aufenthaltsdauer und ausgeglichene Nachfrage.

`Prüfungsphase`: höhere Ankunftsintensität, längere Aufenthaltsdauer und stärkere Nachfrage nach allen Ressourcentypen.

`Prüfungsphase mit Reservierungssystem`: wie die Prüfungsphase, aber Gruppenräume werden als SimPy `PriorityResource` modelliert. Ein Teil der Gruppen hat eine Reservierung und erhält Priorität in der Warteschlange.

## Bedienung

Im Webinterface können Szenario, Ressourcenanzahl, Ankünfte pro Stunde, mittlere Aufenthaltsdauer, maximale Wartezeit und Random Seed angepasst werden. Nach einem Klick auf "Simulation starten" ruft die Seite `POST /simulate` auf und aktualisiert Kennzahlen, Tabelle und Diagramme ohne Seitenreload.

## Wichtige Dateien

- `app.py`: Flask-Routen und JSON-Verarbeitung.
- `simulation.py`: SimPy-Modell und Funktion `run_simulation(config: dict) -> dict`.
- `scenarios.py`: vordefinierte Szenarien und Standardwerte.
- `statistics.py`: Berechnung der Ergebniskennzahlen.
- `docs/documentation.md`: ausführliche Projektdokumentation auf Deutsch.
