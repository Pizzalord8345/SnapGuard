#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple

class RecoveryManager:
    """
    Advanced recovery management for SnapGuard.
    Provides file-level restoration and bootable recovery environment.
    """
    
    def __init__(self, snapshot_manager, config_path: str = "config.json"):
        self.logger = logging.getLogger(__name__)
        self.snapshot_manager = snapshot_manager
        self.config = self._load_config(config_path)
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file."""
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def restore_file(self, snapshot_id: str, file_path: str, target_path: Optional[str] = None) -> bool:
        """
        Restore a single file from a snapshot.
        
        Args:
            snapshot_id: ID of the snapshot to restore from
            file_path: Path of the file within the snapshot
            target_path: Target path for restoration (defaults to original path)
            
        Returns:
            True if restoration was successful, False otherwise
        """
        try:
            # Get the snapshot
            snapshot = self.snapshot_manager.get_snapshot_by_id(snapshot_id)
            if not snapshot:
                self.logger.error(f"Snapshot not found: {snapshot_id}")
                return False
            
            # Construct source path
            source_path = Path(snapshot.path) / file_path
            
            if not source_path.exists():
                self.logger.error(f"File not found in snapshot: {file_path}")
                return False
            
            # Determine target path
            if target_path is None:
                target_path = file_path
            
            target_path = Path(target_path)
            
            # Create parent directories if they don't exist
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy the file
            shutil.copy2(source_path, target_path)
            
            self.logger.info(f"Restored file {file_path} from snapshot {snapshot_id} to {target_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error restoring file: {e}")
            return False
    
    def restore_directory(self, snapshot_id: str, directory_path: str, 
                         target_path: Optional[str] = None,
                         include_patterns: List[str] = None,
                         exclude_patterns: List[str] = None) -> Dict:
        """
        Restore a directory from a snapshot with filtering options.
        
        Args:
            snapshot_id: ID of the snapshot to restore from
            directory_path: Path of the directory within the snapshot
            target_path: Target path for restoration (defaults to original path)
            include_patterns: List of glob patterns to include
            exclude_patterns: List of glob patterns to exclude
            
        Returns:
            Dictionary with restoration statistics
        """
        try:
            # Get the snapshot
            snapshot = self.snapshot_manager.get_snapshot_by_id(snapshot_id)
            if not snapshot:
                self.logger.error(f"Snapshot not found: {snapshot_id}")
                return {"error": "Snapshot not found"}
            
            # Construct source path
            source_path = Path(snapshot.path) / directory_path
            
            if not source_path.exists() or not source_path.is_dir():
                self.logger.error(f"Directory not found in snapshot: {directory_path}")
                return {"error": "Directory not found in snapshot"}
            
            # Determine target path
            if target_path is None:
                target_path = directory_path
            
            target_path = Path(target_path)
            
            # Create target directory if it doesn't exist
            target_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize statistics
            stats = {
                "files_processed": 0,
                "files_restored": 0,
                "directories_created": 0,
                "skipped": 0,
                "errors": 0
            }
            
            # Process all files in the source directory
            for source_file in source_path.rglob("*"):
                stats["files_processed"] += 1
                
                # Get relative path
                rel_path = source_file.relative_to(source_path)
                target_file = target_path / rel_path
                
                # Check include/exclude patterns
                should_include = True
                
                if include_patterns:
                    should_include = False
                    for pattern in include_patterns:
                        if rel_path.match(pattern):
                            should_include = True
                            break
                
                if exclude_patterns and should_include:
                    for pattern in exclude_patterns:
                        if rel_path.match(pattern):
                            should_include = False
                            break
                
                if not should_include:
                    stats["skipped"] += 1
                    continue
                
                try:
                    if source_file.is_dir():
                        target_file.mkdir(parents=True, exist_ok=True)
                        stats["directories_created"] += 1
                    else:
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source_file, target_file)
                        stats["files_restored"] += 1
                except Exception as e:
                    self.logger.error(f"Error restoring {rel_path}: {e}")
                    stats["errors"] += 1
            
            self.logger.info(f"Restored directory {directory_path} from snapshot {snapshot_id} to {target_path}")
            return stats
        except Exception as e:
            self.logger.error(f"Error restoring directory: {e}")
            return {"error": str(e)}
    
    def create_bootable_recovery(self, snapshot_id: str, target_device: str) -> bool:
        """
        Create a bootable recovery environment from a snapshot.
        
        Args:
            snapshot_id: ID of the snapshot to use
            target_device: Target device for the bootable media
            
        Returns:
            True if creation was successful, False otherwise
        """
        try:
            # Get the snapshot
            snapshot = self.snapshot_manager.get_snapshot_by_id(snapshot_id)
            if not snapshot:
                self.logger.error(f"Snapshot not found: {snapshot_id}")
                return False
            
            # Check if target device exists
            target_device_path = Path(target_device)
            if not target_device_path.exists():
                self.logger.error(f"Target device not found: {target_device}")
                return False
            
            # Create a temporary directory for mounting
            with tempfile.TemporaryDirectory() as temp_dir:
                mount_point = Path(temp_dir)
                
                # Format the target device
                self.logger.info(f"Formatting {target_device} as ext4")
                result = subprocess.run(
                    ["mkfs.ext4", "-F", target_device],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    self.logger.error(f"Failed to format device: {result.stderr}")
                    return False
                
                # Mount the target device
                self.logger.info(f"Mounting {target_device} to {mount_point}")
                result = subprocess.run(
                    ["mount", target_device, str(mount_point)],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    self.logger.error(f"Failed to mount device: {result.stderr}")
                    return False
                
                try:
                    # Copy snapshot contents to the mounted device
                    self.logger.info(f"Copying snapshot {snapshot_id} to {mount_point}")
                    
                    # Use rsync for efficient copying
                    result = subprocess.run(
                        ["rsync", "-a", "--exclude=/proc", "--exclude=/sys", "--exclude=/dev",
                         "--exclude=/run", "--exclude=/tmp", f"{snapshot.path}/", f"{mount_point}/"],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode != 0:
                        self.logger.error(f"Failed to copy snapshot: {result.stderr}")
                        return False
                    
                    # Install GRUB bootloader
                    self.logger.info(f"Installing GRUB bootloader on {target_device}")
                    
                    # Create necessary directories
                    (mount_point / "boot").mkdir(exist_ok=True)
                    (mount_point / "boot" / "grub").mkdir(exist_ok=True)
                    
                    # Generate GRUB configuration
                    grub_config = f"""
                    set default=0
                    set timeout=5
                    
                    menuentry "SnapGuard Recovery Environment" {{
                        linux /boot/vmlinuz root={target_device} ro quiet
                        initrd /boot/initrd.img
                    }}
                    """
                    
                    with open(mount_point / "boot" / "grub" / "grub.cfg", 'w') as f:
                        f.write(grub_config)
                    
                    # Install GRUB
                    result = subprocess.run(
                        ["grub-install", "--root-directory", str(mount_point), target_device],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode != 0:
                        self.logger.error(f"Failed to install GRUB: {result.stderr}")
                        return False
                    
                    # Create recovery info file
                    recovery_info = {
                        "snapshot_id": snapshot_id,
                        "created": str(datetime.datetime.now()),
                        "source_snapshot": str(snapshot.path),
                        "description": snapshot.description
                    }
                    
                    with open(mount_point / "recovery_info.json", 'w') as f:
                        json.dump(recovery_info, f, indent=2)
                    
                    self.logger.info(f"Bootable recovery environment created on {target_device}")
                    return True
                    
                finally:
                    # Unmount the target device
                    self.logger.info(f"Unmounting {target_device}")
                    subprocess.run(["umount", target_device], capture_output=True)
        
        except Exception as e:
            self.logger.error(f"Error creating bootable recovery: {e}")
            return False
    
    def create_time_machine_index(self, snapshot_ids: List[str], output_path: str) -> bool:
        """
        Create a time machine style index of files across multiple snapshots.
        
        Args:
            snapshot_ids: List of snapshot IDs to include
            output_path: Path to save the index
            
        Returns:
            True if creation was successful, False otherwise
        """
        try:
            # Initialize the index
            time_machine_index = {
                "snapshots": {},
                "files": {}
            }
            
            # Process each snapshot
            for snapshot_id in snapshot_ids:
                snapshot = self.snapshot_manager.get_snapshot_by_id(snapshot_id)
                if not snapshot:
                    self.logger.warning(f"Snapshot not found: {snapshot_id}")
                    continue
                
                # Add snapshot info to the index
                time_machine_index["snapshots"][snapshot_id] = {
                    "name": snapshot.name,
                    "timestamp": snapshot.timestamp,
                    "description": snapshot.description,
                    "path": str(snapshot.path)
                }
                
                # Process all files in the snapshot
                snapshot_path = Path(snapshot.path)
                for file_path in snapshot_path.rglob("*"):
                    if not file_path.is_file():
                        continue
                    
                    # Get relative path
                    rel_path = str(file_path.relative_to(snapshot_path))
                    
                    # Get file metadata
                    stat = file_path.stat()
                    file_info = {
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                        "path": str(file_path)
                    }
                    
                    # Add to the index
                    if rel_path not in time_machine_index["files"]:
                        time_machine_index["files"][rel_path] = {}
                    
                    time_machine_index["files"][rel_path][snapshot_id] = file_info
            
            # Save the index
            with open(output_path, 'w') as f:
                json.dump(time_machine_index, f, indent=2)
            
            self.logger.info(f"Time machine index created at {output_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error creating time machine index: {e}")
            return False
    
    def restore_from_time_machine(self, index_path: str, file_path: str, 
                                snapshot_id: str, target_path: Optional[str] = None) -> bool:
        """
        Restore a file from a specific snapshot using the time machine index.
        
        Args:
            index_path: Path to the time machine index
            file_path: Path of the file to restore
            snapshot_id: ID of the snapshot to restore from
            target_path: Target path for restoration (defaults to original path)
            
        Returns:
            True if restoration was successful, False otherwise
        """
        try:
            # Load the time machine index
            with open(index_path, 'r') as f:
                index = json.load(f)
            
            # Check if the file exists in the index
            if file_path not in index["files"]:
                self.logger.error(f"File not found in index: {file_path}")
                return False
            
            # Check if the file exists in the specified snapshot
            if snapshot_id not in index["files"][file_path]:
                self.logger.error(f"File not found in snapshot {snapshot_id}: {file_path}")
                return False
            
            # Get the file info
            file_info = index["files"][file_path][snapshot_id]
            source_path = file_info["path"]
            
            # Determine target path
            if target_path is None:
                target_path = file_path
            
            target_path = Path(target_path)
            
            # Create parent directories if they don't exist
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy the file
            shutil.copy2(source_path, target_path)
            
            self.logger.info(f"Restored file {file_path} from snapshot {snapshot_id} to {target_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error restoring from time machine: {e}")
            return False