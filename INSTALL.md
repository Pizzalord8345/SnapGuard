# SnapGuard Installation

## Preconditions

- Python 3.6 or later
- GTK 3.0
- Systemd
- Btrfs-Filesystem
- Polkit

## Installation

1. clone the Repository:
```bash
git clone https://github.com/yourusername/snapguard.git
cd snapguard
```

2. Install the Python-Dependencys:
```bash
pip install -r requirements.txt
```

3. Install the Systemd-Service- und Timer-Files:
```bash
sudo cp src/snapguard.service /etc/systemd/system/
sudo cp src/snapguard.timer /etc/systemd/system/
```

4. Install the Polkit-Guidelines:
```bash
sudo cp src/org.snapguard.policy /usr/share/polkit-1/actions/
```

5. Create the Snapshot-Directory:
```bash
sudo mkdir -p /.snapshots
sudo chown $USER:$USER /.snapshots
```

6. Activate and start the Service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable snapguard.timer
sudo systemctl start snapguard.timer
```

## Verwendung

Start the Graphical user Interface:
```bash
python3 src/gui.py
```

## Configuration
 The default configuration is in `src/config.json`. You can customize this file to: 
 - Change the default snapshot directory
 - - Set the maximum number of snapshots
   - - Configure the schedule for automatic snapshots
     - - Adjust notification settings
       - 
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
