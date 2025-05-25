# SnapGuard Installation

## Preconditions

- Python 3.6 or later  
- GTK 3.0  
- Systemd  
- Btrfs filesystem  
- Polkit  

## Installation

### Clone the repository:
   git clone https://github.com/yourusername/snapguard.git
   cd snapguard
   
### Install the Python dependencies:
pip install -r requirements.txt

### Install the systemd service and timer files:
sudo cp src/snapguard.service /etc/systemd/system/
sudo cp src/snapguard.timer /etc/systemd/system/

### Install the Polkit policy file:
sudo cp src/org.snapguard.policy /usr/share/polkit-1/actions/

### Create the snapshot directory:
sudo mkdir -p /.snapshots
sudo chown $USER:$USER /.snapshots

### Enable and start the service:
sudo systemctl daemon-reload
sudo systemctl enable snapguard.timer
sudo systemctl start snapguard.timer

## Usage

### Start the graphical user interface:
python3 src/gui.py

## Configuration
The default configuration is located in src/config.json.
You can customize this file to:
- Change the default snapshot directory
- Set the maximum number of snapshots
- Configure the schedule for automatic snapshots
- Adjust notification settings

## Troubleshooting
### Check the service status:
systemctl status snapguard.service

### View the logs:
journalctl -u snapguard.service

Ensure Polkit is correctly configured:
pkaction --verbose | grep snapguard

## Security
SnapGuard uses Polkit for privileged operations
Make sure only trusted users have access to the GUI

