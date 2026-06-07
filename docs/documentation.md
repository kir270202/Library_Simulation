# Bibliotheks-/Lernraum-Simulation mit SimPy

## 1. Problemstellung

Vor Prüfungsphasen steigt die Nachfrage nach Lernplätzen an Hochschulen deutlich. Studierende suchen Einzelarbeitsplätze, PC-Arbeitsplätze oder Gruppenräume. Wenn alle Ressourcen belegt sind, entstehen Warteschlangen. Einige Studierende warten nur begrenzt und verlassen die Bibliothek, wenn innerhalb ihrer maximalen Wartezeit kein Platz frei wird.

Ziel dieses Projekts ist eine kleine, aber ernsthafte diskrete Simulation, die diese Situation in einer Hochschulbibliothek modelliert. Die Webanwendung soll zeigen, wie stark die Ressourcen ausgelastet sind, wie viele Studierende oder Gruppen bedient werden und wie viele wegen voller Kapazitäten abgewiesen werden.

## 2. Bezug zu HTW und studentischem Alltag

Das Modell passt zum Alltag an einer Hochschule, weil Lernräume vor Klausuren oft knapp werden. Besonders Gruppenräume und PC-Arbeitsplätze können Engpässe bilden. Die Simulation kann helfen, typische Fragen zu untersuchen:

- Reichen die vorhandenen Lernplätze im Normalbetrieb aus?
- Wie stark verschlechtert sich die Situation in der Prüfungsphase?
- Kann ein einfaches Reservierungssystem für Gruppenräume die Warte- und Ablehnungssituation verbessern?

Die konkreten Zahlen im Modell sind Annahmen. In einer realen Untersuchung müssten diese Parameter durch Beobachtung, Zähldaten oder eine Befragung validiert werden.

## 3. Warum SimPy?

SimPy eignet sich für dieses Projekt, weil Bibliotheksnutzung gut als diskretes Ereignissystem beschrieben werden kann. Studierende kommen zu zufälligen Zeitpunkten an, stellen eine Anfrage an eine Ressource, warten eventuell, nutzen die Ressource für eine bestimmte Dauer und verlassen danach das System. Genau solche Prozesse lassen sich mit SimPy übersichtlich als Generatorfunktionen modellieren.

Vorteile von SimPy in diesem Projekt:

- Ressourcen wie Lernplätze und Gruppenräume können direkt mit `Resource` modelliert werden.
- Warteschlangen entstehen automatisch durch Ressourcenanfragen.
- Zeit wird in Minuten simuliert und muss nicht in Echtzeit vergehen.
- Prioritäten für Reservierungen können mit `PriorityResource` umgesetzt werden.

## 4. Systemgrenzen

Die Simulation betrachtet einen einzelnen Studientag mit 480 Minuten, also 8 Stunden. Modelliert werden nur die Nutzung und Wartesituation innerhalb der Bibliothek.

Nicht modelliert werden:

- konkrete Gebäudepläne oder Laufwege,
- individuelle Stundenpläne,
- Öffnungszeiten außerhalb des simulierten Tages,
- Verlängerung oder Abbruch eines Aufenthalts,
- Mehrfachbesuche derselben Person,
- echte Reservierungsdaten oder Kalenderlogik,
- Login, Datenbank oder langfristige Speicherung.

## 5. Annahmen

Das Modell basiert auf vereinfachten Annahmen:

- Jede Ankunft benötigt genau einen Ressourcentyp.
- Einzelpersonen benötigen entweder einen normalen Lernplatz oder einen PC-Arbeitsplatz.
- Gruppen benötigen genau einen Gruppenraum.
- Eine Gruppe wird in den Kennzahlen als eine Nachfrageeinheit gezählt, zusätzlich wird intern die Personenzahl der Gruppe erfasst.
- Studierende warten maximal eine einstellbare Zeit.
- Wenn innerhalb dieser Zeit keine Ressource frei wird, gilt die Nachfrage als abgewiesen.
- Die Ressourcenanzahl bleibt während des Tages konstant.
- Ankunftsrate, Aufenthaltsdauer und Nachfrageanteile sind geschätzte Parameter.

In einer realen Studie sollten diese Annahmen mit Beobachtungen, Nutzungsdaten oder Umfragen überprüft und angepasst werden.

## 6. Ressourcen

Das Modell unterscheidet drei Ressourcentypen:

| Ressource | Bedeutung |
| --- | --- |
| Einzelarbeitsplätze | Normale Lernplätze für einzelne Studierende |
| PC-Arbeitsplätze | Arbeitsplätze mit Computer |
| Gruppenräume | Räume für Gruppen von 2 bis 6 Personen |

Jede Ressource besitzt eine Kapazität. Ist die Kapazität voll belegt, entsteht eine Warteschlange.

## 7. Zufallsvariablen und Verteilungen

Die Simulation nutzt mehrere Zufallsvariablen:

| Zufallsvariable | Umsetzung im Modell |
| --- | --- |
| Zwischenankunftszeit | Exponentialverteilung, abgeleitet aus Ankünften pro Stunde |
| Ressourcentyp | Zufallswahl nach Szenario-Wahrscheinlichkeiten |
| Aufenthaltsdauer | Dreiecksverteilung um die mittlere Aufenthaltsdauer |
| Gruppengröße | Gleichverteilung zwischen 2 und 6 Personen |
| Reservierung bei Gruppenräumen | Bernoulli-Entscheidung anhand des Reservierungsanteils |

Die Exponentialverteilung ist typisch für zufällige Ankunftsprozesse. Die Dreiecksverteilung für Aufenthalte ist einfach nachvollziehbar und erlaubt kurze, mittlere und lange Nutzungszeiten ohne unplausible negative Werte.

## 8. Studentenprozesse

Jede Ankunft durchläuft folgenden Prozess:

1. Ankunftszeit wird durch den Ankunftsprozess erzeugt.
2. Ressourcentyp wird zufällig bestimmt.
3. Bei Gruppen wird eine Gruppengröße zwischen 2 und 6 gezogen.
4. Die passende Ressource wird angefragt.
5. Ist die Ressource frei, beginnt die Nutzung sofort.
6. Ist sie belegt, wartet die Person oder Gruppe bis zur maximalen Wartezeit.
7. Wird innerhalb der Wartezeit eine Ressource frei, wird die Nachfrage bedient.
8. Andernfalls verlässt die Nachfrage das System und wird als abgewiesen gezählt.
9. Nach Ablauf der Aufenthaltsdauer wird die Ressource wieder freigegeben.

## 9. Szenarien

### Normalbetrieb

Der Normalbetrieb modelliert einen regulären Studientag. Die Ankunftsrate ist moderat, die mittlere Aufenthaltsdauer liegt im normalen Bereich und die Nachfrage verteilt sich vor allem auf Einzelarbeitsplätze.

### Prüfungsphase

Die Prüfungsphase modelliert die Belastung vor Klausuren. Die Ankunftsrate ist höher, Studierende bleiben länger und die Nachfrage nach allen Ressourcen steigt. Dadurch entstehen mehr Warteschlangen und eine höhere Ablehnungsrate.

### Prüfungsphase mit Reservierungssystem

Dieses Szenario entspricht der Prüfungsphase, ergänzt aber eine einfache Reservierungslogik für Gruppenräume. Gruppenräume werden mit SimPys `PriorityResource` modelliert. Ein Anteil der Gruppen hat eine Reservierung und erhält Priorität gegenüber Gruppen ohne Reservierung.

Das ist keine vollständige Kalenderverwaltung. Es ist eine bewusst einfache Modellierung: Reservierte Gruppen haben eine bessere Position in der Warteschlange. So kann untersucht werden, ob Priorisierung die Ablehnung reservierter Nachfrage reduziert und wie sich dies auf die Gesamtauslastung auswirkt.

## 10. Ergebniskennzahlen

Die Simulation liefert:

- Anzahl bedienter Nutzer oder Gruppen pro Ressourcentyp,
- Anzahl abgewiesener Nutzer oder Gruppen pro Ressourcentyp,
- durchschnittliche Wartezeit pro Ressourcentyp,
- durchschnittliche Auslastung pro Ressourcentyp,
- maximale Warteschlangenlänge pro Ressourcentyp,
- gesamte Anzahl der Ankünfte,
- gesamte Anzahl der abgewiesenen Nachfragen,
- Ablehnungsrate in Prozent.

Die Auslastung wird als belegte Ressourcenzeit geteilt durch verfügbare Ressourcenzeit berechnet. Beispiel: 10 Lernplätze über 480 Minuten ergeben 4800 verfügbare Platzminuten.

## 11. Zeitreihendaten

Neben den Kennzahlen sammelt das Modell alle 10 Minuten Zeitreihendaten:

- belegte Einzelarbeitsplätze,
- belegte PC-Arbeitsplätze,
- belegte Gruppenräume,
- Warteschlangenlänge für Einzelarbeitsplätze,
- Warteschlangenlänge für PC-Arbeitsplätze,
- Warteschlangenlänge für Gruppenräume.

Diese Daten werden im Frontend als Liniendiagramme dargestellt.

## 12. Architekturübersicht

Die Anwendung ist bewusst modular aufgebaut:

| Datei | Aufgabe |
| --- | --- |
| `app.py` | Flask-App, Startseite, JSON-Endpunkt `/simulate` |
| `simulation.py` | SimPy-Modell und Funktion `run_simulation(config)` |
| `scenarios.py` | Vordefinierte Szenarien und Standardparameter |
| `statistics.py` | Aufbereitung der Kennzahlen |
| `templates/index.html` | Einseitige Benutzeroberfläche |
| `static/style.css` | Layout und Gestaltung |
| `static/script.js` | Fetch-Aufruf, DOM-Updates und Chart.js-Diagramme |
| `docs/documentation.md` | Projektdokumentation |

Frontend und Backend kommunizieren über JSON. Die Seite sendet Parameter per `POST /simulate`; Flask ruft die Simulation auf und gibt ein JSON-Ergebnis zurück.

## 13. Technologien

- Python
- Flask
- SimPy
- NumPy
- pandas als optionale Analysebibliothek
- HTML
- CSS
- JavaScript
- Chart.js
- JSON

## 14. Start der App

### Lokal mit Python

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Danach:

```text
http://127.0.0.1:5000
```

Unter Windows wird die virtuelle Umgebung mit `venv\Scripts\activate` aktiviert.

### Mit Docker

Alternativ kann die Anwendung mit Docker gestartet werden. Dabei werden Python und die benötigten Bibliotheken im Container installiert.

Mit Docker Compose:

```bash
docker compose up --build
```

Ohne Docker Compose:

```bash
docker build -t library-room-simulation .
docker run --rm -p 5000:5000 library-room-simulation
```

Danach ist die Anwendung ebenfalls unter folgender Adresse erreichbar:

```text
http://127.0.0.1:5000
```

Damit Docker-Portweiterleitung funktioniert, setzt das Docker-Setup die Umgebungsvariable `FLASK_HOST=0.0.0.0`. Beim lokalen Start ohne Docker nutzt die App standardmäßig `127.0.0.1`.

## 15. Interpretation der Ergebnisse

Eine hohe Auslastung bedeutet, dass eine Ressource stark genutzt wird. Das ist nicht automatisch gut: Wenn die Auslastung sehr nahe bei 100 Prozent liegt, entstehen häufig Warteschlangen und Ablehnungen.

Eine hohe Ablehnungsrate zeigt, dass viele Nachfragen innerhalb der maximalen Wartezeit keinen Platz erhalten. Die maximale Warteschlangenlänge zeigt, wie stark sich die Nachfrage zu Spitzenzeiten staut.

Beim Vergleich der Szenarien sollte besonders betrachtet werden:

- Wie verändert sich die Ablehnungsrate vom Normalbetrieb zur Prüfungsphase?
- Welche Ressource wird zuerst zum Engpass?
- Verbessert das Reservierungssystem die Situation für Gruppenräume?
- Führt Priorisierung zu Nebenwirkungen für nicht reservierte Gruppen?

## 16. Grenzen des Modells

Das Modell ist absichtlich klein gehalten und für ein Zweierteam realistisch. Es zeigt Zusammenhänge, ersetzt aber keine echte Datenerhebung.

Wichtige Grenzen:

- Parameter sind geschaetzt.
- Ankunftsrate ist über den Tag konstant.
- Es gibt keine Tagesganglinie mit Morgen-, Mittags- und Abendspitzen.
- Gruppenräume haben keine unterschiedlichen Raumgrößen.
- Reservierungen werden nur als Priorität modelliert.
- Es gibt keine No-Shows oder verspäteten Reservierungen.
- Verhalten von Studierenden wird stark vereinfacht.

## 17. Mögliche Verbesserungen

Mögliche Erweiterungen wären:

- reale Ankunftsdaten oder Umfragewerte einbauen,
- Tagesganglinien für unterschiedliche Uhrzeiten modellieren,
- Gruppenräume mit verschiedenen Kapazitäten unterscheiden,
- No-Shows im Reservierungssystem modellieren,
- mehrere Simulationstage oder Replikationen durchführen,
- Konfidenzintervalle für Kennzahlen berechnen,
- Export der Ergebnisse als CSV anbieten,
- Szenariovergleich direkt nebeneinander darstellen.

## 18. Arbeitsverteilung für zwei Personen

Die Arbeit sollte phasenbasiert erfolgen und nicht strikt in Frontend und Backend getrennt werden.

### Phase 1: Systemanalyse gemeinsam

- Ressourcen definieren
- Annahmen festlegen
- Szenarien definieren
- Kennzahlen festlegen

### Phase 2: Simulationskomponenten

Person A:

- Ankunftsprozess
- Auswahl des Studierendentyp bzw. Ressourcentyps
- Aufenthaltsdauer
- Warteverhalten

Person B:

- Ressourcenmodell
- Warteschlangen-Monitoring
- Auslastungsberechnung
- Reservierungslogik

### Phase 3: GUI-Komponenten

Person A:

- Parameterformular
- Szenarioauswahl
- Fetch-Request zum Backend

Person B:

- Ergebniskarten
- Diagramme
- Ergebnistabelle

### Phase 4: Integration gemeinsam

- Frontend und Backend verbinden
- Szenarien testen
- Plausibilität der Ergebnisse pruefen

### Phase 5: Dokumentation und Präsentation gemeinsam

- Modell erklären
- Zufallsfaktoren erklären
- Ergebnisse interpretieren
- Grenzen des Modells diskutieren

## 19. Fazit

Die Anwendung zeigt, wie diskrete Simulation genutzt werden kann, um Engpässe in Lernräumen sichtbar zu machen. Sie bleibt bewusst verständlich und kompakt, enthält aber die wesentlichen Bestandteile eines Simulationsprojekts: Zufallsprozesse, Ressourcen, Warteschlangen, Szenarien, Kennzahlen und Visualisierung.
