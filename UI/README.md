# UI Feature (Integration GUI)

Dieses Feature stellt eine **Tkinter-GUI** bereit, um die Core-Integration von QMToolV6 zu testen.

## Highlights
- Login und Registrierung neuer Benutzer (Admin-Seed vorhanden: **admin/admin**)
- Anzeige von Audit-Logs und UI-Events
- Unterseite mit Reitern für **meta.json** und **labels.tsv**

## Starten
```bash
python -m UI.gui.app
```

## Tests
```bash
pytest UI/tests
```

## Struktur
```
UI/
├── gui/                 # Tkinter GUI
├── services/            # Service-Layer
│   └── policy/          # Input-Validierung
├── repository/          # SQLite Repository für UI-Events
├── dto/                 # Data Transfer Objects
├── enum/                # Enumerations
├── exceptions/          # Custom Exceptions
└── tests/               # Pytest Tests
```
