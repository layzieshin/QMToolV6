# QMToolV6 Use Case Test GUI

Die GUI (Tkinter) dient dazu, die wichtigsten Use Cases des Projekts
interaktiv auszuführen und deren Ergebnis direkt zu sehen.

## Start

```bash
python main.py
```

## Aufbau

- **Linke Seite:** Liste der Use Cases mit Statusanzeige (PASS/FAIL).
- **Rechte Seite:** Details zum ausgewählten Use Case (Ziel, Schritte,
  erwartetes Ergebnis, beteiligte Komponenten).
- **Execution Log:** Laufprotokoll aller Tests mit Detailausgabe.

## Bedienung

- **Run Selected** führt den aktuell markierten Use Case aus.
- **Run All** führt alle Use Cases nacheinander aus.
- **Clear Log** leert das Protokoll.

## Hinweise

- Viele Use Cases verwenden In-Memory-SQLite, um Nebenwirkungen zu vermeiden.
- Einige Integrationsfälle (z. B. Authenticator ↔ AuditTrail) prüfen die
  aktuelle Implementierung und können bei fehlender Integration bewusst
  fehlschlagen.
- Die GUI ist als Test-Werkzeug gedacht und verändert keine Anwendungslogik.
