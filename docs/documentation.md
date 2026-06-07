# Bibliotheks-/Lernraum-Simulation mit SimPy

## 1. Problemstellung

Vor Pruefungsphasen steigt die Nachfrage nach Lernplaetzen an Hochschulen deutlich. Studierende suchen Einzelarbeitsplaetze, PC-Arbeitsplaetze oder Gruppenraeume. Wenn alle Ressourcen belegt sind, entstehen Warteschlangen. Einige Studierende warten nur begrenzt und verlassen die Bibliothek, wenn innerhalb ihrer maximalen Wartezeit kein Platz frei wird.

Ziel dieses Projekts ist eine kleine, aber ernsthafte diskrete Simulation, die diese Situation in einer Hochschulbibliothek modelliert. Die Webanwendung soll zeigen, wie stark die Ressourcen ausgelastet sind, wie viele Studierende oder Gruppen bedient werden und wie viele wegen voller Kapazitaeten abgewiesen werden.

## 2. Bezug zu HTW und studentischem Alltag

Das Modell passt zum Alltag an einer Hochschule, weil Lernraeume vor Klausuren oft knapp werden. Besonders Gruppenraeume und PC-Arbeitsplaetze koennen Engpaesse bilden. Die Simulation kann helfen, typische Fragen zu untersuchen:

- Reichen die vorhandenen Lernplaetze im Normalbetrieb aus?
- Wie stark verschlechtert sich die Situation in der Pruefungsphase?
- Kann ein einfaches Reservierungssystem fuer Gruppenraeume die Warte- und Ablehnungssituation verbessern?

Die konkreten Zahlen im Modell sind Annahmen. In einer realen Untersuchung muessten diese Parameter durch Beobachtung, Zaehldaten oder eine Befragung validiert werden.

## 3. Warum SimPy?

SimPy eignet sich fuer dieses Projekt, weil Bibliotheksnutzung gut als diskretes Ereignissystem beschrieben werden kann. Studierende kommen zu zufaelligen Zeitpunkten an, stellen eine Anfrage an eine Ressource, warten eventuell, nutzen die Ressource fuer eine bestimmte Dauer und verlassen danach das System. Genau solche Prozesse lassen sich mit SimPy uebersichtlich als Generatorfunktionen modellieren.

Vorteile von SimPy in diesem Projekt:

- Ressourcen wie Lernplaetze und Gruppenraeume koennen direkt mit `Resource` modelliert werden.
- Warteschlangen entstehen automatisch durch Ressourcenanfragen.
- Zeit wird in Minuten simuliert und muss nicht in Echtzeit vergehen.
- Prioritaeten fuer Reservierungen koennen mit `PriorityResource` umgesetzt werden.

## 4. Systemgrenzen

Die Simulation betrachtet einen einzelnen Studientag mit 480 Minuten, also 8 Stunden. Modelliert werden nur die Nutzung und Wartesituation innerhalb der Bibliothek.

Nicht modelliert werden:

- konkrete Gebaeudeplaene oder Laufwege,
- individuelle Stundenplaene,
- Oeffnungszeiten ausserhalb des simulierten Tages,
- Verlaengerung oder Abbruch eines Aufenthalts,
- Mehrfachbesuche derselben Person,
- echte Reservierungsdaten oder Kalenderlogik,
- Login, Datenbank oder langfristige Speicherung.

## 5. Annahmen

Das Modell basiert auf vereinfachten Annahmen:

- Jede Ankunft benoetigt genau einen Ressourcentyp.
- Einzelpersonen benoetigen entweder einen normalen Lernplatz oder einen PC-Arbeitsplatz.
- Gruppen benoetigen genau einen Gruppenraum.
- Eine Gruppe wird in den Kennzahlen als eine Nachfrageeinheit gezaehlt, zusaetzlich wird intern die Personenzahl der Gruppe erfasst.
- Studierende warten maximal eine einstellbare Zeit.
- Wenn innerhalb dieser Zeit keine Ressource frei wird, gilt die Nachfrage als abgewiesen.
- Die Ressourcenanzahl bleibt waehrend des Tages konstant.
- Ankunftsrate, Aufenthaltsdauer und Nachfrageanteile sind geschaetzte Parameter.

In einer realen Studie sollten diese Annahmen mit Beobachtungen, Nutzungsdaten oder Umfragen ueberprueft und angepasst werden.

## 6. Ressourcen

Das Modell unterscheidet drei Ressourcentypen:

| Ressource | Bedeutung |
| --- | --- |
| Einzelarbeitsplaetze | Normale Lernplaetze fuer einzelne Studierende |
| PC-Arbeitsplaetze | Arbeitsplaetze mit Computer |
| Gruppenraeume | Raeume fuer Gruppen von 2 bis 6 Personen |

Jede Ressource besitzt eine Kapazitaet. Ist die Kapazitaet voll belegt, entsteht eine Warteschlange.

## 7. Zufallsvariablen und Verteilungen

Die Simulation nutzt mehrere Zufallsvariablen:

| Zufallsvariable | Umsetzung im Modell |
| --- | --- |
| Zwischenankunftszeit | Exponentialverteilung, abgeleitet aus Ankuenften pro Stunde |
| Ressourcentyp | Zufallswahl nach Szenario-Wahrscheinlichkeiten |
| Aufenthaltsdauer | Dreiecksverteilung um die mittlere Aufenthaltsdauer |
| Gruppengroesse | Gleichverteilung zwischen 2 und 6 Personen |
| Reservierung bei Gruppenraeumen | Bernoulli-Entscheidung anhand des Reservierungsanteils |

Die Exponentialverteilung ist typisch fuer zufaellige Ankunftsprozesse. Die Dreiecksverteilung fuer Aufenthalte ist einfach nachvollziehbar und erlaubt kurze, mittlere und lange Nutzungszeiten ohne unplausible negative Werte.

## 8. Studentenprozesse

Jede Ankunft durchlaeuft folgenden Prozess:

1. Ankunftszeit wird durch den Ankunftsprozess erzeugt.
2. Ressourcentyp wird zufaellig bestimmt.
3. Bei Gruppen wird eine Gruppengroesse zwischen 2 und 6 gezogen.
4. Die passende Ressource wird angefragt.
5. Ist die Ressource frei, beginnt die Nutzung sofort.
6. Ist sie belegt, wartet die Person oder Gruppe bis zur maximalen Wartezeit.
7. Wird innerhalb der Wartezeit eine Ressource frei, wird die Nachfrage bedient.
8. Andernfalls verlaesst die Nachfrage das System und wird als abgewiesen gezaehlt.
9. Nach Ablauf der Aufenthaltsdauer wird die Ressource wieder freigegeben.

## 9. Szenarien

### Normalbetrieb

Der Normalbetrieb modelliert einen regulaeren Studientag. Die Ankunftsrate ist moderat, die mittlere Aufenthaltsdauer liegt im normalen Bereich und die Nachfrage verteilt sich vor allem auf Einzelarbeitsplaetze.

### Pruefungsphase

Die Pruefungsphase modelliert die Belastung vor Klausuren. Die Ankunftsrate ist hoeher, Studierende bleiben laenger und die Nachfrage nach allen Ressourcen steigt. Dadurch entstehen mehr Warteschlangen und eine hoehere Ablehnungsrate.

### Pruefungsphase mit Reservierungssystem

Dieses Szenario entspricht der Pruefungsphase, ergaenzt aber eine einfache Reservierungslogik fuer Gruppenraeume. Gruppenraeume werden mit SimPys `PriorityResource` modelliert. Ein Anteil der Gruppen hat eine Reservierung und erhaelt Prioritaet gegenueber Gruppen ohne Reservierung.

Das ist keine vollstaendige Kalenderverwaltung. Es ist eine bewusst einfache Modellierung: Reservierte Gruppen haben eine bessere Position in der Warteschlange. So kann untersucht werden, ob Priorisierung die Ablehnung reservierter Nachfrage reduziert und wie sich dies auf die Gesamtauslastung auswirkt.

## 10. Ergebniskennzahlen

Die Simulation liefert:

- Anzahl bedienter Nutzer oder Gruppen pro Ressourcentyp,
- Anzahl abgewiesener Nutzer oder Gruppen pro Ressourcentyp,
- durchschnittliche Wartezeit pro Ressourcentyp,
- durchschnittliche Auslastung pro Ressourcentyp,
- maximale Warteschlangenlaenge pro Ressourcentyp,
- gesamte Anzahl der Ankuenfte,
- gesamte Anzahl der abgewiesenen Nachfragen,
- Ablehnungsrate in Prozent.

Die Auslastung wird als belegte Ressourcenzeit geteilt durch verfuegbare Ressourcenzeit berechnet. Beispiel: 10 Lernplaetze ueber 480 Minuten ergeben 4800 verfuegbare Platzminuten.

## 11. Zeitreihendaten

Neben den Kennzahlen sammelt das Modell alle 10 Minuten Zeitreihendaten:

- belegte Einzelarbeitsplaetze,
- belegte PC-Arbeitsplaetze,
- belegte Gruppenraeume,
- Warteschlangenlaenge fuer Einzelarbeitsplaetze,
- Warteschlangenlaenge fuer PC-Arbeitsplaetze,
- Warteschlangenlaenge fuer Gruppenraeume.

Diese Daten werden im Frontend als Liniendiagramme dargestellt.

## 12. Architekturuebersicht

Die Anwendung ist bewusst modular aufgebaut:

| Datei | Aufgabe |
| --- | --- |
| `app.py` | Flask-App, Startseite, JSON-Endpunkt `/simulate` |
| `simulation.py` | SimPy-Modell und Funktion `run_simulation(config)` |
| `scenarios.py` | Vordefinierte Szenarien und Standardparameter |
| `statistics.py` | Aufbereitung der Kennzahlen |
| `templates/index.html` | Einseitige Benutzeroberflaeche |
| `static/style.css` | Layout und Gestaltung |
| `static/script.js` | Fetch-Aufruf, DOM-Updates und Chart.js-Diagramme |
| `docs/documentation.md` | Projektdokumentation |

Frontend und Backend kommunizieren ueber JSON. Die Seite sendet Parameter per `POST /simulate`; Flask ruft die Simulation auf und gibt ein JSON-Ergebnis zurueck.

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

Alternativ kann die Anwendung mit Docker gestartet werden. Dabei werden Python und die benoetigten Bibliotheken im Container installiert.

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

Damit Docker-Portweiterleitung funktioniert, setzt das Docker-Setup die Umgebungsvariable `FLASK_HOST=0.0.0.0`. Beim lokalen Start ohne Docker nutzt die App standardmaessig `127.0.0.1`.

## 15. Interpretation der Ergebnisse

Eine hohe Auslastung bedeutet, dass eine Ressource stark genutzt wird. Das ist nicht automatisch gut: Wenn die Auslastung sehr nahe bei 100 Prozent liegt, entstehen haeufig Warteschlangen und Ablehnungen.

Eine hohe Ablehnungsrate zeigt, dass viele Nachfragen innerhalb der maximalen Wartezeit keinen Platz erhalten. Die maximale Warteschlangenlaenge zeigt, wie stark sich die Nachfrage zu Spitzenzeiten staut.

Beim Vergleich der Szenarien sollte besonders betrachtet werden:

- Wie veraendert sich die Ablehnungsrate vom Normalbetrieb zur Pruefungsphase?
- Welche Ressource wird zuerst zum Engpass?
- Verbessert das Reservierungssystem die Situation fuer Gruppenraeume?
- Fuehrt Priorisierung zu Nebenwirkungen fuer nicht reservierte Gruppen?

## 16. Grenzen des Modells

Das Modell ist absichtlich klein gehalten und fuer ein Zweierteam realistisch. Es zeigt Zusammenhaenge, ersetzt aber keine echte Datenerhebung.

Wichtige Grenzen:

- Parameter sind geschaetzt.
- Ankunftsrate ist ueber den Tag konstant.
- Es gibt keine Tagesganglinie mit Morgen-, Mittags- und Abendspitzen.
- Gruppenraeume haben keine unterschiedlichen Raumgroessen.
- Reservierungen werden nur als Prioritaet modelliert.
- Es gibt keine No-Shows oder verspaeteten Reservierungen.
- Verhalten von Studierenden wird stark vereinfacht.

## 17. Moegliche Verbesserungen

Moegliche Erweiterungen waeren:

- reale Ankunftsdaten oder Umfragewerte einbauen,
- Tagesganglinien fuer unterschiedliche Uhrzeiten modellieren,
- Gruppenraeume mit verschiedenen Kapazitaeten unterscheiden,
- No-Shows im Reservierungssystem modellieren,
- mehrere Simulationstage oder Replikationen durchfuehren,
- Konfidenzintervalle fuer Kennzahlen berechnen,
- Export der Ergebnisse als CSV anbieten,
- Szenariovergleich direkt nebeneinander darstellen.

## 18. Arbeitsverteilung fuer zwei Personen

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
- Plausibilitaet der Ergebnisse pruefen

### Phase 5: Dokumentation und Praesentation gemeinsam

- Modell erklaeren
- Zufallsfaktoren erklaeren
- Ergebnisse interpretieren
- Grenzen des Modells diskutieren

## 19. Fazit

Die Anwendung zeigt, wie diskrete Simulation genutzt werden kann, um Engpaesse in Lernraeumen sichtbar zu machen. Sie bleibt bewusst verstaendlich und kompakt, enthaelt aber die wesentlichen Bestandteile eines Simulationsprojekts: Zufallsprozesse, Ressourcen, Warteschlangen, Szenarien, Kennzahlen und Visualisierung.
