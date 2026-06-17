# Bibliotheks-/Lernraum-Simulation mit SimPy

## Zielsetzung

Ziel des Projekts ist eine verständliche diskrete Simulation für eine Hochschulbibliothek. Die Anwendung zeigt, wie sich Nachfrage, Kapazitäten und Wartebereitschaft auf Lernplätze, PC-Arbeitsplätze und Gruppenräume auswirken.

Die Simulation soll keine echte Bibliotheksplanung ersetzen. Sie ist ein bewusst vereinfachtes Modell für das Modul "Diskrete Simulation" und dient dazu, typische Engpässe sichtbar zu machen.

## Problemstellung

Vor Prüfungsphasen steigt die Nachfrage nach Lernplätzen oft deutlich. Wenn alle Plätze oder Räume belegt sind, entstehen Warteschlangen. Einige Studierende oder Gruppen warten nur begrenzt und verlassen die Bibliothek, wenn innerhalb der maximalen Wartezeit kein Platz frei wird.

Das Modell untersucht deshalb:

- wie viele Anfragen bedient werden,
- wie viele Anfragen abgewiesen werden,
- welche Ressource zum Engpass wird,
- wie stark die Ressourcen ausgelastet sind,
- wie sich ein einfaches Reservierungssystem für Gruppenräume auswirken kann.

## Modellbeschreibung

Ein simulierter Tag dauert standardmäßig 480 Minuten. Neue Anfragen entstehen zufällig. Jede Anfrage benötigt genau einen Ressourcentyp:

- Einzelarbeitsplatz,
- PC-Arbeitsplatz,
- Gruppenraum.

Ist die gewünschte Ressource frei, beginnt die Nutzung sofort. Ist sie belegt, wartet die Anfrage in der Warteschlange. Wird innerhalb der maximalen Wartezeit kein Platz frei, gilt die Anfrage als abgewiesen.

Gruppenräume werden von Gruppen mit zufälliger Gruppengröße genutzt. Im Reservierungsszenario werden Gruppenräume als `PriorityResource` modelliert. Ein Anteil der Gruppen hat eine Reservierung und erhält dadurch Priorität in der Warteschlange.

## Ressourcen

| Ressource | Bedeutung |
| --- | --- |
| Einzelarbeitsplätze | normale Lernplätze für einzelne Studierende |
| PC-Arbeitsplätze | Arbeitsplätze mit Computer |
| Gruppenräume | Räume für Gruppen von 2 bis 6 Personen |

Die Kapazitäten sind im Webinterface editierbar. Werte kleiner als 0 werden abgelehnt.

## Zufallsvariablen und Verteilungen

| Zufallsvariable | Umsetzung |
| --- | --- |
| Zwischenankunftszeit | Exponentialverteilung aus der Ankunftsrate pro Stunde |
| Ressourcentyp | Zufallswahl nach Szenario-Wahrscheinlichkeiten |
| Aufenthaltsdauer | Dreiecksverteilung um die mittlere Aufenthaltsdauer |
| Gruppengröße | Gleichverteilung von 2 bis 6 Personen |
| Reservierung | Bernoulli-Entscheidung über den Reservierungsanteil |

Die numerischen Parameter sind Annahmen. In einer realen Untersuchung müssten sie mit Beobachtungen, Zähldaten oder Befragungen validiert werden.

## Szenarien

### Normalbetrieb

Moderate Ankunftsrate, normale Aufenthaltsdauer und überwiegende Nachfrage nach Einzelarbeitsplätzen.

### Prüfungsphase

Höhere Ankunftsrate, längere Aufenthaltsdauer und stärkere Nachfrage nach PC-Arbeitsplätzen und Gruppenräumen. Dadurch entstehen häufiger Warteschlangen und Abweisungen.

### Prüfungsphase mit Reservierungssystem

Wie die Prüfungsphase, aber Gruppenräume besitzen eine einfache Prioritätslogik. Das Reservierungssystem ist keine echte Kalenderverwaltung. Es wird nur als Priorität in der Warteschlange modelliert.

## Umsetzung im Code

| Datei | Aufgabe |
| --- | --- |
| `app.py` | Flask-App, Startseite, Validierung, JSON-Endpunkt `/simulate` |
| `simulation.py` | SimPy-Modell, Ankunftsprozess, Ressourcen, Warte- und Nutzungslogik |
| `scenarios.py` | drei vordefinierte Szenarien mit Standardwerten |
| `statistics.py` | Kennzahlen und kurze Interpretation |
| `templates/index.html` | Weboberfläche |
| `static/script.js` | Formularlogik, Fetch-Aufruf, Statusmeldungen, Diagramme |
| `static/style.css` | Layout und visuelle Gestaltung |

Frontend und Backend kommunizieren über JSON. Nach dem Klick auf "Simulation starten" zeigt die Oberfläche sofort den Status "Simulation läuft … bitte kurz warten.", sperrt den Button und aktualisiert danach Kennzahlen, Tabelle, Diagramme und Interpretation.

## Kennzahlen

Die Simulation liefert:

- gesamte Ankünfte,
- bediente Anfragen,
- abgewiesene Anfragen,
- Ablehnungsrate,
- durchschnittliche Wartezeit je Ressource,
- Auslastung je Ressource,
- maximale Warteschlangenlänge je Ressource,
- Belegungsverlauf über den Tag,
- Warteschlangenverlauf über den Tag.

Die Auslastung wird als genutzte Ressourcenzeit geteilt durch verfügbare Ressourcenzeit berechnet. Hohe Auslastung ist nicht automatisch gut, weil sie bei knappen Ressourcen Warteschlangen und Ablehnungen begünstigen kann.

## Ergebnisse

Die Ergebnisse werden in der Weboberfläche als KPI-Karten, Tabelle und Diagramme dargestellt. Die Balkendiagramme zeigen Auslastung und Abweisungen je Ressource. Die Liniendiagramme zeigen Belegung und Warteschlangen im Zeitverlauf.

Durch den Random Seed sind Ergebnisse reproduzierbar. Bleibt der Seed leer, erzeugt jeder Lauf neue Zufallswerte.

## Interpretation

Nach jedem Lauf erstellt die Anwendung eine kurze Interpretation:

- wahrscheinlicher Hauptengpass,
- Einordnung der Ablehnungsrate,
- Hinweis zum Reservierungssystem,
- naheliegende Maßnahme.

Diese Interpretation ist bewusst kompakt. Für eine belastbare Bewertung sollten insbesondere die Prüfungsphase ohne Reservierung und die Prüfungsphase mit Reservierungssystem miteinander verglichen werden.

## Grenzen des Modells

Das Modell ist bewusst vereinfacht:

- Parameter sind geschätzt und müssten real validiert werden.
- Die Ankunftsrate ist über den Tag konstant.
- Es gibt keine Tagesganglinie mit Morgen-, Mittags- und Abendspitzen.
- Jede Anfrage benötigt nur einen Ressourcentyp.
- Gruppenräume haben keine unterschiedlichen Raumgrößen.
- Reservierungen werden nur als Priorität modelliert.
- Es gibt keine Datenbank, keinen Login und keine echten Kalenderdaten.
- Verhalten wie No-Shows, vorzeitiges Gehen oder Mehrfachbesuche wird nicht modelliert.

## Verbesserungsmöglichkeiten

Mögliche Erweiterungen wären:

- reale Zähldaten oder Umfragewerte verwenden,
- tageszeitabhängige Ankunftsraten einbauen,
- Gruppenräume mit unterschiedlichen Kapazitäten modellieren,
- No-Shows im Reservierungssystem ergänzen,
- mehrere unabhängige Replikationen durchführen,
- Szenarien direkt nebeneinander vergleichen,
- Ergebnisse als CSV exportieren.

Die Replikationsfunktion wurde bewusst nicht eingebaut, weil sie für die vorhandenen Zeitreihen und Diagramme zusätzliche Aggregationslogik erfordern würde. Für die aktuelle Abgabe bleibt ein einzelner, reproduzierbarer Simulationslauf verständlicher.

## Startanleitung

Lokal:

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

Mit Docker:

```bash
docker compose up --build
```

Danach ebenfalls öffnen:

```text
http://127.0.0.1:5000
```

## Fazit

Die Anwendung zeigt mit überschaubarem Code, wie diskrete Simulation Engpässe in Lernräumen sichtbar machen kann. Sie verbindet SimPy-Modell, Flask-Oberfläche, Szenarioauswahl, editierbare Parameter, Kennzahlen, Diagramme und kurze Interpretation zu einem kompakten Abschlussprojekt.
