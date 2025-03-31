# SnapGuard

A user-friendly Linux snapshot management tool for BTRFS and OverlayFS.

## Features

- Intuitive GUI for creating, managing, and restoring system snapshots
- Support for both BTRFS and OverlayFS
- Live Mode for testing changes in a safe environment
- Automatic snapshot creation
- Easy restoration of previous system states
- Live mode for risk-free testing of updates
- Automatic snapshots during system updates
- Intuitive, minimalist user interface
- Overview of snapshot storage usage

## Installation

```bash
# Install system dependencies
sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-3.0 btrfs-progs

# Clone repository
git clone https://github.com/Pizzalord8345/SnapGuard.git
cd snapguard

# Install Python dependencies
pip install -r requirements.txt

# Start application
python3 src/main.py
```

## System Requirements

- Linux with OverlayFS and/or Btrfs support
- Python 3.6 or higher
- GTK 3.0
- Superuser rights for snapshot operations

## License

GPL-3.0
