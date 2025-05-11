# SnapGuard Installation

## Voraussetzungen

- Python 3.6 oder höher
- GTK 3.0
- Systemd
- Btrfs-Dateisystem
- Polkit

## Installation

1. Klonen Sie das Repository:
```bash
git clone https://github.com/yourusername/snapguard.git
cd snapguard
```

2. Installieren Sie die Python-Abhängigkeiten:
```bash
pip install -r requirements.txt
```

3. Installieren Sie die Systemd-Service- und Timer-Dateien:
```bash
sudo cp src/snapguard.service /etc/systemd/system/
sudo cp src/snapguard.timer /etc/systemd/system/
```

4. Installieren Sie die Polkit-Richtlinien:
```bash
sudo cp src/org.snapguard.policy /usr/share/polkit-1/actions/
```

5. Erstellen Sie das Snapshot-Verzeichnis:
```bash
sudo mkdir -p /.snapshots
sudo chown $USER:$USER /.snapshots
```

6. Aktivieren und starten Sie den Service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable snapguard.timer
sudo systemctl start snapguard.timer
```

## Verwendung

Starten Sie die GUI mit:
```bash
python3 src/gui.py
```

## Konfiguration

Die Standardkonfiguration befindet sich in `src/config.json`. Sie können diese Datei anpassen, um:
- Das Standard-Snapshot-Verzeichnis zu ändern
- Die maximale Anzahl von Snapshots festzulegen
- Den Zeitplan für automatische Snapshots zu konfigurieren
- Benachrichtigungseinstellungen anzupassen

## Fehlerbehebung

1. Überprüfen Sie den Service-Status:
```bash
systemctl status snapguard.service
```

2. Überprüfen Sie die Logs:
```bash
journalctl -u snapguard.service
```

3. Stellen Sie sicher, dass Polkit korrekt konfiguriert ist:
```bash
pkaction --verbose | grep snapguard
```

## Sicherheit

- SnapGuard verwendet Polkit für privilegierte Operationen
- Stellen Sie sicher, dass nur vertrauenswürdige Benutzer Zugriff auf die GUI haben
- Regelmäßige Backups der Snapshots werden empfohlen 