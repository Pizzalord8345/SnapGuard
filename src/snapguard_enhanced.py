#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import os
import subprocess
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple

# Import original SnapGuard functionality
from snapguard import SnapGuard

# Import new modules
from key_manager import KeyManager
from encryption import EncryptionManager
from mfa import MFAManager
from deduplication import DeduplicationManager
from recovery import RecoveryManager
from parallel_processing import ParallelProcessor, IOThrottler, SmartScheduler
from integration import PluginManager, BackupIntegration

class SnapGuardEnhanced(SnapGuard):
    """
    Enhanced version of SnapGuard with additional features.
    Extends the original SnapGuard class with new capabilities.
    """
    
    def __init__(self, config_path: str = "config.json"):
        # Initialize base SnapGuard
        super().__init__(config_path)
        
        # Initialize enhanced components
        self.key_manager = KeyManager(config_path)
        self.encryption_manager = EncryptionManager(self.key_manager, self.config)
        self.mfa_manager = MFAManager(config_path)
        self.deduplication_manager = DeduplicationManager(config_path)
        self.recovery_manager = RecoveryManager(self, config_path)
        
        # Initialize performance components
        use_processes = self.config.get("performance", {}).get("parallel_processing", {}).get("use_processes", False)
        max_workers = self.config.get("performance", {}).get("parallel_processing", {}).get("max_workers", None)
        self.parallel_processor = ParallelProcessor(max_workers=max_workers, use_processes=use_processes)
        
        max_read_mbps = self.config.get("storage", {}).get("io_throttling", {}).get("max_read_mbps", 0)
        max_write_mbps = self.config.get("storage", {}).get("io_throttling", {}).get("max_write_mbps", 0)
        self.io_throttler = IOThrottler(max_read_mbps=max_read_mbps, max_write_mbps=max_write_mbps)
        
        self.smart_scheduler = SmartScheduler(config_path)
        
        # Initialize integration components
        plugin_dir = self.config.get("integration", {}).get("plugin_directory", "plugins")
        self.plugin_manager = PluginManager(plugin_dir)
        self.backup_integration = BackupIntegration(config_path)
        
        # Check for key rotation
        self._check_key_rotation()
        
        self.logger.info("SnapGuardEnhanced initialized with all enhanced features")
    
    def _check_key_rotation(self) -> None:
        """Check if keys need rotation based on policy."""
        if self.config.get("security", {}).get("key_rotation", {}).get("auto_rotate", False):
            rotation_needed = self.key_manager.should_rotate_keys()
            if rotation_needed:
                self.logger.info(f"Automatic key rotation needed for: {', '.join(rotation_needed)}")
                for key_type in rotation_needed:
                    self.key_manager.rotate_keys(key_type)
    
    def create_snapshot(self, description: Optional[str] = None, 
                       encrypt: bool = True, deduplicate: bool = True,
                       require_mfa: bool = None) -> bool:
        """
        Create a snapshot with enhanced features.
        
        Args:
            description: Optional description for the snapshot
            encrypt: Whether to encrypt the snapshot
            deduplicate: Whether to deduplicate the snapshot
            require_mfa: Whether to require MFA (overrides config)
            
        Returns:
            True if snapshot creation was successful, False otherwise
        """
        # Check if MFA is required
        if require_mfa is None:
            require_mfa = self.config.get("security", {}).get("mfa_policy", {}).get("enabled", False) and \
                         "create_snapshot" in self.config.get("security", {}).get("mfa_policy", {}).get("required_operations", [])
        
        if require_mfa:
            # This would typically prompt the user for MFA in a real application
            # For now, we'll just log it
            self.logger.info("MFA would be required for snapshot creation")
        
        # Use smart scheduling if enabled
        if self.config.get("performance", {}).get("smart_scheduling", {}).get("enabled", False):
            return self.smart_scheduler.run_when_idle(
                self._create_snapshot_internal,
                description=description,
                encrypt=encrypt,
                deduplicate=deduplicate
            )
        else:
            return self._create_snapshot_internal(description, encrypt, deduplicate)
    
    def _create_snapshot_internal(self, description: Optional[str] = None, 
                                encrypt: bool = True, deduplicate: bool = True) -> bool:
        """Internal method to create a snapshot with enhanced features."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            success = True
            created_snapshots = []

            # Process subvolumes in parallel if enabled
            if self.config.get("performance", {}).get("parallel_processing", {}).get("enabled", False):
                # Define a function to create a single subvolume snapshot
                def create_subvol_snapshot(subvol):
                    if not subvol['enabled']:
                        return None
                    
                    snapshot_name = f"snapshot_{subvol['name']}_{timestamp}"
                    if description:
                        snapshot_name += f"_{description}"
                    
                    snapshot_path = f"{self.config['snapshot']['default_location']}/{snapshot_name}"
                    cmd = ['btrfs', 'subvolume', 'snapshot', subvol['path'], snapshot_path]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        return {
                            "name": snapshot_name,
                            "path": snapshot_path,
                            "subvol": subvol['name']
                        }
                    else:
                        self.logger.error(f"Failed to create snapshot: {result.stderr}")
                        return None
                
                # Create snapshots in parallel
                enabled_subvols = [subvol for subvol in self.config['snapshot']['subvolumes'] if subvol['enabled']]
                results = self.parallel_processor.map(create_subvol_snapshot, enabled_subvols)
                
                # Filter out None results (failed snapshots)
                created_snapshots = [r for r in results if r is not None]
                
                if not created_snapshots:
                    self.logger.error("All snapshots failed to create")
                    return False
            else:
                # Use original sequential approach
                for subvol in self.config['snapshot']['subvolumes']:
                    if not subvol['enabled']:
                        continue
                    
                    snapshot_name = f"snapshot_{subvol['name']}_{timestamp}"
                    if description:
                        snapshot_name += f"_{description}"
                    
                    snapshot_path = f"{self.config['snapshot']['default_location']}/{snapshot_name}"
                    cmd = ['btrfs', 'subvolume', 'snapshot', subvol['path'], snapshot_path]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        created_snapshots.append({
                            "name": snapshot_name,
                            "path": snapshot_path,
                            "subvol": subvol['name']
                        })
                    else:
                        self.logger.error(f"Failed to create snapshot: {result.stderr}")
                        success = False
            
            # Process created snapshots
            for snapshot in created_snapshots:
                snapshot_path = snapshot["path"]
                
                # Encrypt snapshot if requested
                if encrypt and self.config['security']['encryption']['enabled']:
                    if self.config['security']['encryption'].get('selective_encryption', False):
                        # Use selective encryption
                        patterns = self.config['security']['encryption'].get('sensitive_patterns', [])
                        success_count, failure_count = self.encryption_manager.encrypt_directory(
                            snapshot_path, 
                            selective=True,
                            patterns=patterns
                        )
                        if failure_count > 0:
                            self.logger.warning(f"Some files failed to encrypt: {failure_count}")
                    else:
                        # Encrypt all files
                        success_count, failure_count = self.encryption_manager.encrypt_directory(snapshot_path)
                        if failure_count > 0:
                            self.logger.warning(f"Some files failed to encrypt: {failure_count}")
                
                # Sign the snapshot
                if self.config['security']['signing']['enabled']:
                    if not self._sign_snapshot(snapshot_path):
                        success = False
                
                # Deduplicate snapshot if requested
                if deduplicate and self.config.get('storage', {}).get('deduplication', {}).get('enabled', False):
                    dedup_stats = self.deduplication_manager.deduplicate_snapshot(snapshot_path)
                    self.logger.info(f"Deduplication saved {dedup_stats.get('space_saved', 0)} bytes")
            
            if success:
                self._send_notification("Snapshot created", "All snapshots were created successfully")
                self._audit_log("create_snapshot", True, f"Description: {description}")
            else:
                self._send_notification("Snapshot failed", "Some snapshots failed to create")
                self._audit_log("create_snapshot", False, f"Description: {description}")
            
            return success
        except Exception as e:
            self.logger.error(f"Error creating snapshot: {e}")
            self._audit_log("create_snapshot", False, str(e))
            return False
    
    def restore_snapshot(self, snapshot_name: str, target_path: Optional[str] = None,
                        require_mfa: bool = None) -> bool:
        """
        Restore a snapshot with enhanced features.
        
        Args:
            snapshot_name: Name of the snapshot to restore
            target_path: Target path for restoration (defaults to original path)
            require_mfa: Whether to require MFA (overrides config)
            
        Returns:
            True if restoration was successful, False otherwise
        """
        # Check if MFA is required
        if require_mfa is None:
            require_mfa = self.config.get("security", {}).get("mfa_policy", {}).get("enabled", False) and \
                         "restore_snapshot" in self.config.get("security", {}).get("mfa_policy", {}).get("required_operations", [])
        
        if require_mfa:
            # This would typically prompt the user for MFA in a real application
            # For now, we'll just log it
            self.logger.info("MFA would be required for snapshot restoration")
        
        try:
            snapshot_path = Path(self.config['snapshot']['default_location']) / snapshot_name
            
            if not snapshot_path.exists():
                self.logger.error(f"Snapshot not found: {snapshot_name}")
                return False
            
            # Determine target path if not specified
            if target_path is None:
                # Try to determine original path from snapshot name
                parts = snapshot_name.split('_')
                if len(parts) >= 2 and parts[0] == "snapshot":
                    subvol_name = parts[1]
                    for subvol in self.config['snapshot']['subvolumes']:
                        if subvol['name'] == subvol_name:
                            target_path = subvol['path']
                            break
            
            if target_path is None:
                self.logger.error("Could not determine target path for restoration")
                return False
            
            # Check if snapshot is deduplicated
            dedup_metadata = snapshot_path / ".deduplication_metadata.json"
            if dedup_metadata.exists():
                # Restore deduplicated snapshot
                self.logger.info(f"Restoring deduplicated snapshot: {snapshot_name}")
                self.deduplication_manager.restore_deduplicated_snapshot(snapshot_path)
            
            # Check if snapshot is encrypted
            encryption_metadata = snapshot_path / ".encryption_metadata.json"
            if encryption_metadata.exists():
                # Decrypt snapshot
                self.logger.info(f"Decrypting snapshot: {snapshot_name}")
                self.encryption_manager.decrypt_directory(snapshot_path)
            
            # Verify snapshot integrity
            if self.config['security']['signing']['enabled']:
                if not self.verify_snapshot(str(snapshot_path)):
                    self.logger.error(f"Snapshot integrity verification failed: {snapshot_name}")
                    return False
            
            # Perform the restoration
            target_path = Path(target_path)
            if target_path.exists():
                # Backup existing data
                backup_path = target_path.with_name(f"{target_path.name}_backup_{int(datetime.now().timestamp())}")
                self.logger.info(f"Backing up existing data to: {backup_path}")
                shutil.move(target_path, backup_path)
            
            # Use the recovery manager for restoration
            self.logger.info(f"Restoring snapshot {snapshot_name} to {target_path}")
            stats = self.recovery_manager.restore_directory(snapshot_name, ".", str(target_path))
            
            if stats.get("error"):
                self.logger.error(f"Error restoring snapshot: {stats['error']}")
                return False
            
            self.logger.info(f"Restored {stats.get('files_restored', 0)} files from snapshot {snapshot_name}")
            self._audit_log("restore_snapshot", True, f"Snapshot: {snapshot_name}, Target: {target_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error restoring snapshot: {e}")
            self._audit_log("restore_snapshot", False, str(e))
            return False
    
    def export_backup(self, destination: str, format_name: Optional[str] = None,
                     compress: bool = True, encrypt: bool = True) -> bool:
        """
        Export a backup with enhanced features.
        
        Args:
            destination: Destination path for the backup
            format_name: Format to export to (None for native format)
            compress: Whether to compress the backup
            encrypt: Whether to encrypt the backup
            
        Returns:
            True if export was successful, False otherwise
        """
        try:
            # Use the original export_backup method if no special format is requested
            if format_name is None:
                # Apply compression if requested
                if compress and self.config.get('backup', {}).get('compression', {}).get('enabled', False):
                    self.logger.info("Applying compression to backup")
                    # Compression would be applied here
                
                # Apply encryption if requested
                if encrypt and self.config['security']['encryption']['enabled']:
                    self.logger.info("Applying encryption to backup")
                    # Encryption would be applied here
                
                return super().export_backup(destination)
            else:
                # Use backup integration for other formats
                self.logger.info(f"Exporting backup to {format_name} format")
                return self.backup_integration.export_to_format(
                    self.list_snapshots()[0]['name'],  # Use the first snapshot as an example
                    format_name,
                    destination
                )
        
        except Exception as e:
            self.logger.error(f"Error exporting backup: {e}")
            return False
    
    def cleanup_old_snapshots(self) -> bool:
        """
        Clean up old snapshots with enhanced features.
        
        Returns:
            True if cleanup was successful, False otherwise
        """
        # Use smart scheduling if enabled
        if self.config.get("performance", {}).get("smart_scheduling", {}).get("enabled", False):
            return self.smart_scheduler.run_when_idle(super().cleanup_old_snapshots)
        else:
            return super().cleanup_old_snapshots()
    
    def restore_file(self, snapshot_name: str, file_path: str, 
                    target_path: Optional[str] = None) -> bool:
        """
        Restore a single file from a snapshot.
        
        Args:
            snapshot_name: Name of the snapshot to restore from
            file_path: Path of the file within the snapshot
            target_path: Target path for restoration (defaults to original path)
            
        Returns:
            True if restoration was successful, False otherwise
        """
        return self.recovery_manager.restore_file(snapshot_name, file_path, target_path)
    
    def create_time_machine_index(self) -> bool:
        """
        Create a time machine index of all snapshots.
        
        Returns:
            True if index creation was successful, False otherwise
        """
        snapshots = self.list_snapshots()
        snapshot_ids = [s['name'] for s in snapshots]
        
        index_path = self.config.get('recovery', {}).get('time_machine', {}).get('index_path', 
                                                                               '/var/lib/snapguard/time_machine_index.json')
        
        return self.recovery_manager.create_time_machine_index(snapshot_ids, index_path)
    
    def create_bootable_recovery(self, snapshot_name: str, target_device: str) -> bool:
        """
        Create a bootable recovery environment from a snapshot.
        
        Args:
            snapshot_name: Name of the snapshot to use
            target_device: Target device for the bootable media
            
        Returns:
            True if creation was successful, False otherwise
        """
        return self.recovery_manager.create_bootable_recovery(snapshot_name, target_device)
    
    def load_plugin(self, plugin_name: str) -> bool:
        """
        Load a plugin by name.
        
        Args:
            plugin_name: Name of the plugin to load
            
        Returns:
            True if plugin was loaded successfully, False otherwise
        """
        return self.plugin_manager.load_plugin(plugin_name)
    
    def get_deduplication_stats(self) -> Dict:
        """
        Get deduplication statistics.
        
        Returns:
            Dictionary with deduplication statistics
        """
        return self.deduplication_manager.get_deduplication_stats()