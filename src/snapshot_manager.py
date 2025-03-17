#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import json
import datetime
import shutil
from pathlib import Path
import subprocess
from typing import List, Dict, Optional, Tuple

from utils import run_command, is_btrfs_available, is_overlayfs_available

class Snapshot:
    """Represents a snapshot (Btrfs or OverlayFS)."""
    def __init__(self, id: str, name: str, type: str, path: str, timestamp: str, 
                 description: str = "", size: int = 0, is_active: bool = False,
                 is_auto: bool = False):
        self.id = id
        self.name = name
        self.type = type  # 'btrfs' or 'overlay'
        self.path = path
        self.timestamp = timestamp
        self.description = description
        self.size = size
        self.is_active = is_active
        self.is_auto = is_auto
    
    def to_dict(self) -> Dict:
        """Converts the snapshot to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'path': self.path,
            'timestamp': self.timestamp,
            'description': self.description,
            'size': self.size,
            'is_active': self.is_active,
            'is_auto': self.is_auto
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Snapshot':
        """Creates a snapshot from a dictionary."""
        return cls(
            id=data['id'],
            name=data['name'],
            type=data['type'],
            path=data['path'],
            timestamp=data['timestamp'],
            description=data.get('description', ''),
            size=data.get('size', 0),
            is_active=data.get('is_active', False),
            is_auto=data.get('is_auto', False)
        )

class SnapshotManager:
    """Manages the creation, deletion and restoration of snapshots."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_dir = Path.home() / ".config" / "bettersync"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.snapshots_file = self.config_dir / "snapshots.json"
        self.config_file = self.config_dir / "config.json"
        
        self.snapshots = []
        self.load_snapshots()
        self.load_config()
        
        # Check available snapshot methods
        self.btrfs_available = is_btrfs_available()
        self.overlayfs_available = is_overlayfs_available()
        
        self.logger.info(f"Btrfs available: {self.btrfs_available}")
        self.logger.info(f"OverlayFS available: {self.overlayfs_available}")
    
    def load_snapshots(self) -> None:
        """Loads the list of snapshots from the file."""
        if not self.snapshots_file.exists():
            self.snapshots = []
            return
        
        try:
            with open(self.snapshots_file, 'r') as f:
                data = json.load(f)
                self.snapshots = [Snapshot.from_dict(item) for item in data]
            self.logger.info(f"{len(self.snapshots)} snapshots loaded.")
        except Exception as e:
            self.logger.error(f"Error loading snapshots: {e}")
            self.snapshots = []
    
    def save_snapshots(self) -> None:
        """Saves the list of snapshots to the file."""
        try:
            with open(self.snapshots_file, 'w') as f:
                data = [snapshot.to_dict() for snapshot in self.snapshots]
                json.dump(data, f, indent=4)
            self.logger.info(f"{len(self.snapshots)} snapshots saved.")
        except Exception as e:
            self.logger.error(f"Error saving snapshots: {e}")
    
    def load_config(self) -> None:
        """Loads the configuration from the file."""
        if not self.config_file.exists():
            self.config = {
                'btrfs_mount_point': '/mnt/btrfs',
                'overlay_mount_point': '/mnt/overlay',
                'auto_snapshot_enabled': True,
                'max_snapshots': 10,
                'snapshot_directory': '/var/lib/bettersync/snapshots'
            }
            self.save_config()
            return
        
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
            self.logger.info("Configuration loaded.")
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            self.config = {}
    
    def save_config(self) -> None:
        """Saves the configuration to the file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            self.logger.info("Configuration saved.")
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
    
    def get_snapshots(self, snapshot_type: Optional[str] = None) -> List[Snapshot]:
        """Returns all snapshots or snapshots of a specific type."""
        if snapshot_type is None:
            return self.snapshots
        return [s for s in self.snapshots if s.type == snapshot_type]
    
    def get_snapshot_by_id(self, snapshot_id: str) -> Optional[Snapshot]:
        """Returns a snapshot by its ID."""
        for snapshot in self.snapshots:
            if snapshot.id == snapshot_id:
                return snapshot
        return None
    
    def create_btrfs_snapshot(self, name: str, source_path: str, description: str = "", 
                             is_auto: bool = False) -> Optional[Snapshot]:
        """Creates a Btrfs snapshot."""
        if not self.btrfs_available:
            self.logger.error("Btrfs is not available.")
            return None
        
        timestamp = datetime.datetime.now().isoformat()
        snapshot_id = f"btrfs_{int(datetime.datetime.now().timestamp())}"
        
        snapshot_dir = Path(self.config['snapshot_directory']) / "btrfs"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        snapshot_path = snapshot_dir / snapshot_id
        
        # Create Btrfs snapshot
        cmd = ["btrfs", "subvolume", "snapshot", source_path, str(snapshot_path)]
        result = run_command(cmd)
        
        if result.returncode != 0:
            self.logger.error(f"Error creating Btrfs snapshot: {result.stderr}")
            return None
        
        # Determine snapshot size
        size = self._get_directory_size(snapshot_path)
        
        # Create and save snapshot
        snapshot = Snapshot(
            id=snapshot_id,
            name=name,
            type="btrfs",
            path=str(snapshot_path),
            timestamp=timestamp,
            description=description,
            size=size,
            is_active=False,
            is_auto=is_auto
        )
        
        self.snapshots.append(snapshot)
        self.save_snapshots()
        
        self.logger.info(f"Btrfs snapshot created: {name} ({snapshot_id})")
        return snapshot
    
    def create_overlay_snapshot(self, name: str, source_path: str, description: str = "",
                              is_auto: bool = False) -> Optional[Snapshot]:
        """Creates an OverlayFS snapshot."""
        if not self.overlayfs_available:
            self.logger.error("OverlayFS is not available.")
            return None
        
        timestamp = datetime.datetime.now().isoformat()
        snapshot_id = f"overlay_{int(datetime.datetime.now().timestamp())}"
        
        snapshot_dir = Path(self.config['snapshot_directory']) / "overlay"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        # Create directories for OverlayFS
        overlay_path = snapshot_dir / snapshot_id
        lower_dir = overlay_path / "lower"
        upper_dir = overlay_path / "upper"
        work_dir = overlay_path / "work"
        merged_dir = overlay_path / "merged"
        
        for d in [overlay_path, lower_dir, upper_dir, work_dir, merged_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        # Copy source files to lower_dir
        try:
            if Path(source_path).is_dir():
                shutil.copytree(source_path, lower_dir, dirs_exist_ok=True)
            else:
                shutil.copy2(source_path, lower_dir)
        except Exception as e:
            self.logger.error(f"Error copying source files: {e}")
            return None
        
        # Determine snapshot size
        size = self._get_directory_size(overlay_path)
        
        # Create and save snapshot
        snapshot = Snapshot(
            id=snapshot_id,
            name=name,
            type="overlay",
            path=str(overlay_path),
            timestamp=timestamp,
            description=description,
            size=size,
            is_active=False,
            is_auto=is_auto
        )
        
        self.snapshots.append(snapshot)
        self.save_snapshots()
        
        self.logger.info(f"OverlayFS snapshot created: {name} ({snapshot_id})")
        return snapshot
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """Deletes a snapshot."""
        snapshot = self.get_snapshot_by_id(snapshot_id)
        if not snapshot:
            self.logger.error(f"Snapshot not found: {snapshot_id}")
            return False
        
        if snapshot.is_active:
            self.logger.error(f"Active snapshot cannot be deleted: {snapshot_id}")
            return False
        
        try:
            # Delete physical files
            if snapshot.type == "btrfs":
                cmd = ["btrfs", "subvolume", "delete", snapshot.path]
                result = run_command(cmd)
                if result.returncode != 0:
                    self.logger.error(f"Error deleting Btrfs snapshot: {result.stderr}")
                    return False
            else:  # overlay
                shutil.rmtree(snapshot.path)
            
            # Remove from list
            self.snapshots = [s for s in self.snapshots if s.id != snapshot_id]
            self.save_snapshots()
            
            self.logger.info(f"Snapshot deleted: {snapshot.name} ({snapshot_id})")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting snapshot: {e}")
            return False
    
    def restore_snapshot(self, snapshot_id: str, target_path: str) -> bool:
        """Restores a snapshot."""
        snapshot = self.get_snapshot_by_id(snapshot_id)
        if not snapshot:
            self.logger.error(f"Snapshot not found: {snapshot_id}")
            return False
        
        try:
            if snapshot.type == "btrfs":
                # Target directory must be empty for Btrfs
                if Path(target_path).exists():
                    shutil.rmtree(target_path)
                
                # Restore Btrfs snapshot
                cmd = ["btrfs", "subvolume", "snapshot", snapshot.path, target_path]
                result = run_command(cmd)
                if result.returncode != 0:
                    self.logger.error(f"Error restoring Btrfs snapshot: {result.stderr}")
                    return False
            else:  # overlay
                # For OverlayFS, copy files from lower_dir
                lower_dir = Path(snapshot.path) / "lower"
                if Path(target_path).exists():
                    shutil.rmtree(target_path)
                
                # Copy files
                if lower_dir.is_dir():
                    shutil.copytree(lower_dir, target_path)
                else:
                    Path(target_path).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(lower_dir, target_path)
            
            self.logger.info(f"Snapshot restored: {snapshot.name} ({snapshot_id}) to {target_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error restoring snapshot: {e}")
            return False
    
    def activate_live_mode(self, snapshot_id: str, mount_point: str) -> bool:
        """Activates live mode for an OverlayFS snapshot."""
        snapshot = self.get_snapshot_by_id(snapshot_id)
        if not snapshot:
            self.logger.error(f"Snapshot not found: {snapshot_id}")
            return False
        
        if snapshot.type != "overlay":
            self.logger.error(f"Only OverlayFS snapshots can be activated in live mode: {snapshot_id}")
            return False
        
        try:
            # Prepare OverlayFS mount
            lower_dir = Path(snapshot.path) / "lower"
            upper_dir = Path(snapshot.path) / "upper"
            work_dir = Path(snapshot.path) / "work"
            
            # Create mount point if it doesn't exist
            Path(mount_point).mkdir(parents=True, exist_ok=True)
            
            # Mount OverlayFS
            cmd = [
                "mount", "-t", "overlay", "overlay",
                "-o", f"lowerdir={lower_dir},upperdir={upper_dir},workdir={work_dir}",
                mount_point
            ]
            result = run_command(cmd)
            
            if result.returncode != 0:
                self.logger.error(f"Error activating live mode: {result.stderr}")
                return False
            
            # Mark snapshot as active
            snapshot.is_active = True
            self.save_snapshots()
            
            self.logger.info(f"Live mode activated for: {snapshot.name} ({snapshot_id}) on {mount_point}")
            return True
        except Exception as e:
            self.logger.error(f"Error activating live mode: {e}")
            return False
    
    def deactivate_live_mode(self, snapshot_id: str, mount_point: str, commit_changes: bool = False) -> bool:
        """Deactivates live mode for an OverlayFS snapshot."""
        snapshot = self.get_snapshot_by_id(snapshot_id)
        if not snapshot:
            self.logger.error(f"Snapshot not found: {snapshot_id}")
            return False
        
        if not snapshot.is_active:
            self.logger.error(f"Snapshot is not active in live mode: {snapshot_id}")
            return False
        
        try:
            # Unmount OverlayFS
            cmd = ["umount", mount_point]
            result = run_command(cmd)
            
            if result.returncode != 0:
                self.logger.error(f"Error deactivating live mode: {result.stderr}")
                return False
            
            # Commit changes if desired
            if commit_changes:
                # When commit=True, changes from upper_dir are applied to lower_dir
                upper_dir = Path(snapshot.path) / "upper"
                lower_dir = Path(snapshot.path) / "lower"
                
                # Copy files from upper_dir to lower_dir
                for item in upper_dir.glob("**/*"):
                    if item.is_file():
                        rel_path = item.relative_to(upper_dir)
                        target_path = lower_dir / rel_path
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, target_path)
                
                # Clear upper_dir and work_dir
                for item in upper_dir.glob("*"):
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                
                work_dir = Path(snapshot.path) / "work"
                for item in work_dir.glob("*"):
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
            
            # Mark snapshot as inactive
            snapshot.is_active = False
            self.save_snapshots()
            
            self.logger.info(f"Live mode deactivated for: {snapshot.name} ({snapshot_id}), changes committed: {commit_changes}")
            return True
        except Exception as e:
            self.logger.error(f"Error deactivating live mode: {e}")
            return False
    
    def update_snapshot_size(self, snapshot_id: str) -> bool:
        """Updates the size of a snapshot."""
        snapshot = self.get_snapshot_by_id(snapshot_id)
        if not snapshot:
            return False
        
        try:
            size = self._get_directory_size(snapshot.path)
            snapshot.size = size
            self.save_snapshots()
            return True
        except Exception as e:
            self.logger.error(f"Error updating snapshot size: {e}")
            return False
    
    def _get_directory_size(self, path: str) -> int:
        """Determines the size of a directory in bytes."""
        total_size = 0
        path_obj = Path(path)
        
        if not path_obj.exists():
            return 0
        
        if path_obj.is_file():
            return path_obj.stat().st_size
        
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = Path(dirpath) / f
                if fp.exists() and not fp.is_symlink():
                    total_size += fp.stat().st_size
        
        return total_size
    
    def setup_automatic_snapshots(self, enabled: bool = True) -> bool:
        """Sets up automatic snapshots during system updates."""
        try:
            # Update configuration
            self.config['auto_snapshot_enabled'] = enabled
            self.save_config()
            
            # Create or remove systemd service and timer
            service_dir = Path("/etc/systemd/system")
            service_file = service_dir / "bettersync-auto-snapshot.service"
            timer_file = service_dir / "bettersync-auto-snapshot.timer"
            
            if enabled:
                # Create service file
                service_content = f"""[Unit]
Description=BetterSync Automatic Snapshot Service
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 {Path(__file__).resolve()} --auto-snapshot
User=root

[Install]
WantedBy=multi-user.target
"""
                # Create timer file
                timer_content = """[Unit]
Description=BetterSync Automatic Snapshot Timer

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
"""
                # Create hook for apt/dnf
                apt_hook_dir = Path("/etc/apt/apt.conf.d")
                apt_hook_file = apt_hook_dir / "99-bettersync-snapshot"
                
                apt_hook_content = f"""// BetterSync: Automatic snapshots during apt updates
DPkg::Pre-Invoke {{"/usr/bin/python3 {Path(__file__).resolve()} --auto-snapshot-pre-update"}};
DPkg::Post-Invoke {{"/usr/bin/python3 {Path(__file__).resolve()} --auto-snapshot-post-update"}};
"""
                # Write files
                with open(service_file, 'w') as f:
                    f.write(service_content)
                
                with open(timer_file, 'w') as f:
                    f.write(timer_content)
                
                if apt_hook_dir.exists():
                    with open(apt_hook_file, 'w') as f:
                        f.write(apt_hook_content)
                
                # Enable service
                run_command(["systemctl", "daemon-reload"])
                run_command(["systemctl", "enable", "--now", "bettersync-auto-snapshot.timer"])
            else:
                # Disable service and remove files
                run_command(["systemctl", "disable", "--now", "bettersync-auto-snapshot.timer"])
                
                for file in [service_file, timer_file]:
                    if file.exists():
                        file.unlink()
                
                # Remove apt hook
                apt_hook_file = Path("/etc/apt/apt.conf.d/99-bettersync-snapshot")
                if apt_hook_file.exists():
                    apt_hook_file.unlink()
                
                run_command(["systemctl", "daemon-reload"])
            
            self.logger.info(f"Automatic snapshots {'enabled' if enabled else 'disabled'}")
            return True
        except Exception as e:
            self.logger.error(f"Error setting up automatic snapshots: {e}")
            return False
    
    def create_auto_snapshot(self, snapshot_type: str, source_path: str, reason: str = "auto") -> Optional[Snapshot]:
        """Creates an automatic snapshot."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        name = f"Auto-Snapshot_{reason}_{timestamp}"
        description = f"Automatically created: {reason} on {timestamp}"
        
        if snapshot_type == "btrfs":
            return self.create_btrfs_snapshot(name, source_path, description, is_auto=True)
        else:
            return self.create_overlay_snapshot(name, source_path, description, is_auto=True)
    
    def cleanup_old_snapshots(self, max_count: Optional[int] = None) -> int:
        """Cleans up old snapshots."""
        if max_count is None:
            max_count = self.config.get('max_snapshots', 10)
        
        # Sort snapshots by type and creation date
        btrfs_snapshots = sorted(
            [s for s in self.snapshots if s.type == "btrfs" and not s.is_active],
            key=lambda s: s.timestamp
        )
        overlay_snapshots = sorted(
            [s for s in self.snapshots if s.type == "overlay" and not s.is_active],
            key=lambda s: s.timestamp
        )
        
        # Delete old snapshots
        deleted_count = 0
        
        # Clean up Btrfs snapshots
        while len(btrfs_snapshots) > max_count:
            snapshot = btrfs_snapshots.pop(0)  # Remove oldest snapshot
            if self.delete_snapshot(snapshot.id):
                deleted_count += 1
        
        # Clean up OverlayFS snapshots
        while len(overlay_snapshots) > max_count:
            snapshot = overlay_snapshots.pop(0)  # Remove oldest snapshot
            if self.delete_snapshot(snapshot.id):
                deleted_count += 1
        
        self.logger.info(f"{deleted_count} old snapshots cleaned up")
        return deleted_count
