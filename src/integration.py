#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
import subprocess
import importlib
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

class PluginManager:
    """
    Manages plugins and integrations with other backup solutions.
    """
    
    def __init__(self, plugin_dir: str = "plugins"):
        self.logger = logging.getLogger(__name__)
        self.plugin_dir = Path(plugin_dir)
        self.plugins = {}
        self.loaded_plugins = {}
        
        # Create plugin directory if it doesn't exist
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        
        # Load available plugins
        self._discover_plugins()
    
    def _discover_plugins(self) -> None:
        """Discover available plugins in the plugin directory."""
        for plugin_file in self.plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("__"):
                continue
            
            plugin_name = plugin_file.stem
            self.plugins[plugin_name] = {
                "name": plugin_name,
                "path": str(plugin_file),
                "loaded": False
            }
            
            self.logger.debug(f"Discovered plugin: {plugin_name}")
    
    def load_plugin(self, plugin_name: str) -> bool:
        """
        Load a plugin by name.
        
        Args:
            plugin_name: Name of the plugin to load
            
        Returns:
            True if plugin was loaded successfully, False otherwise
        """
        if plugin_name not in self.plugins:
            self.logger.error(f"Plugin not found: {plugin_name}")
            return False
        
        if self.plugins[plugin_name]["loaded"]:
            self.logger.debug(f"Plugin already loaded: {plugin_name}")
            return True
        
        try:
            # Add plugin directory to path
            import sys
            if str(self.plugin_dir) not in sys.path:
                sys.path.insert(0, str(self.plugin_dir))
            
            # Import the plugin module
            plugin_module = importlib.import_module(plugin_name)
            
            # Check if the module has the required interface
            if not hasattr(plugin_module, "initialize") or not callable(plugin_module.initialize):
                self.logger.error(f"Plugin {plugin_name} does not have required 'initialize' function")
                return False
            
            # Initialize the plugin
            plugin_instance = plugin_module.initialize()
            
            # Store the loaded plugin
            self.loaded_plugins[plugin_name] = plugin_instance
            self.plugins[plugin_name]["loaded"] = True
            
            self.logger.info(f"Loaded plugin: {plugin_name}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error loading plugin {plugin_name}: {e}")
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin by name.
        
        Args:
            plugin_name: Name of the plugin to unload
            
        Returns:
            True if plugin was unloaded successfully, False otherwise
        """
        if plugin_name not in self.plugins:
            self.logger.error(f"Plugin not found: {plugin_name}")
            return False
        
        if not self.plugins[plugin_name]["loaded"]:
            self.logger.debug(f"Plugin not loaded: {plugin_name}")
            return True
        
        try:
            # Check if the plugin has a cleanup function
            plugin_instance = self.loaded_plugins[plugin_name]
            if hasattr(plugin_instance, "cleanup") and callable(plugin_instance.cleanup):
                plugin_instance.cleanup()
            
            # Remove from loaded plugins
            del self.loaded_plugins[plugin_name]
            self.plugins[plugin_name]["loaded"] = False
            
            # Attempt to unload the module
            import sys
            if plugin_name in sys.modules:
                del sys.modules[plugin_name]
            
            self.logger.info(f"Unloaded plugin: {plugin_name}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error unloading plugin {plugin_name}: {e}")
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[Any]:
        """
        Get a loaded plugin instance.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin instance or None if not loaded
        """
        return self.loaded_plugins.get(plugin_name)
    
    def get_available_plugins(self) -> List[Dict]:
        """
        Get list of available plugins.
        
        Returns:
            List of plugin information dictionaries
        """
        return [
            {
                "name": info["name"],
                "path": info["path"],
                "loaded": info["loaded"]
            }
            for info in self.plugins.values()
        ]
    
    def install_plugin(self, plugin_path: Union[str, Path]) -> bool:
        """
        Install a plugin from a file.
        
        Args:
            plugin_path: Path to the plugin file
            
        Returns:
            True if plugin was installed successfully, False otherwise
        """
        plugin_path = Path(plugin_path)
        
        if not plugin_path.exists() or not plugin_path.is_file():
            self.logger.error(f"Plugin file not found: {plugin_path}")
            return False
        
        if plugin_path.suffix != ".py":
            self.logger.error(f"Invalid plugin file type: {plugin_path}")
            return False
        
        try:
            # Copy the plugin file to the plugin directory
            dest_path = self.plugin_dir / plugin_path.name
            shutil.copy2(plugin_path, dest_path)
            
            # Update available plugins
            self._discover_plugins()
            
            self.logger.info(f"Installed plugin: {plugin_path.stem}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error installing plugin: {e}")
            return False
    
    def uninstall_plugin(self, plugin_name: str) -> bool:
        """
        Uninstall a plugin.
        
        Args:
            plugin_name: Name of the plugin to uninstall
            
        Returns:
            True if plugin was uninstalled successfully, False otherwise
        """
        if plugin_name not in self.plugins:
            self.logger.error(f"Plugin not found: {plugin_name}")
            return False
        
        try:
            # Unload the plugin if it's loaded
            if self.plugins[plugin_name]["loaded"]:
                self.unload_plugin(plugin_name)
            
            # Remove the plugin file
            plugin_path = Path(self.plugins[plugin_name]["path"])
            if plugin_path.exists():
                plugin_path.unlink()
            
            # Remove from available plugins
            del self.plugins[plugin_name]
            
            self.logger.info(f"Uninstalled plugin: {plugin_name}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error uninstalling plugin: {e}")
            return False


class BackupIntegration:
    """
    Provides integration with other backup solutions.
    """
    
    SUPPORTED_FORMATS = ["tar", "zip", "restic", "borg", "duplicity"]
    
    def __init__(self, config_path: str = "config.json"):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file."""
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def export_to_format(self, snapshot_id: str, format_name: str, output_path: str) -> bool:
        """
        Export a snapshot to a different backup format.
        
        Args:
            snapshot_id: ID of the snapshot to export
            format_name: Target format name
            output_path: Path to save the exported backup
            
        Returns:
            True if export was successful, False otherwise
        """
        if format_name not in self.SUPPORTED_FORMATS:
            self.logger.error(f"Unsupported export format: {format_name}")
            return False
        
        # Get the snapshot path (this would come from the snapshot manager in a real implementation)
        snapshot_path = f"/var/lib/snapguard/snapshots/{snapshot_id}"
        
        try:
            if format_name == "tar":
                return self._export_to_tar(snapshot_path, output_path)
            elif format_name == "zip":
                return self._export_to_zip(snapshot_path, output_path)
            elif format_name == "restic":
                return self._export_to_restic(snapshot_path, output_path)
            elif format_name == "borg":
                return self._export_to_borg(snapshot_path, output_path)
            elif format_name == "duplicity":
                return self._export_to_duplicity(snapshot_path, output_path)
            else:
                self.logger.error(f"Export format not implemented: {format_name}")
                return False
        
        except Exception as e:
            self.logger.error(f"Error exporting to {format_name}: {e}")
            return False
    
    def _export_to_tar(self, snapshot_path: str, output_path: str) -> bool:
        """Export to tar format."""
        try:
            # Create tar archive
            result = subprocess.run(
                ["tar", "-czf", output_path, "-C", snapshot_path, "."],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"Error creating tar archive: {result.stderr}")
                return False
            
            self.logger.info(f"Exported snapshot to tar: {output_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error exporting to tar: {e}")
            return False
    
    def _export_to_zip(self, snapshot_path: str, output_path: str) -> bool:
        """Export to zip format."""
        try:
            # Create zip archive
            result = subprocess.run(
                ["zip", "-r", output_path, "."],
                cwd=snapshot_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"Error creating zip archive: {result.stderr}")
                return False
            
            self.logger.info(f"Exported snapshot to zip: {output_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error exporting to zip: {e}")
            return False
    
    def _export_to_restic(self, snapshot_path: str, output_path: str) -> bool:
        """Export to restic repository."""
        try:
            # Initialize restic repository if it doesn't exist
            result = subprocess.run(
                ["restic", "init", "--repo", output_path],
                env={"RESTIC_PASSWORD": self.config.get("integration", {}).get("restic_password", "")},
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0 and "already initialized" not in result.stderr:
                self.logger.error(f"Error initializing restic repository: {result.stderr}")
                return False
            
            # Backup to restic repository
            result = subprocess.run(
                ["restic", "backup", snapshot_path, "--repo", output_path],
                env={"RESTIC_PASSWORD": self.config.get("integration", {}).get("restic_password", "")},
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"Error backing up to restic: {result.stderr}")
                return False
            
            self.logger.info(f"Exported snapshot to restic: {output_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error exporting to restic: {e}")
            return False
    
    def _export_to_borg(self, snapshot_path: str, output_path: str) -> bool:
        """Export to borg repository."""
        try:
            # Initialize borg repository if it doesn't exist
            if not Path(output_path).exists():
                result = subprocess.run(
                    ["borg", "init", "--encryption=repokey", output_path],
                    env={"BORG_PASSPHRASE": self.config.get("integration", {}).get("borg_passphrase", "")},
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    self.logger.error(f"Error initializing borg repository: {result.stderr}")
                    return False
            
            # Create archive name based on snapshot ID
            archive_name = f"snapguard-{Path(snapshot_path).name}-{int(time.time())}"
            
            # Backup to borg repository
            result = subprocess.run(
                ["borg", "create", f"{output_path}::{archive_name}", snapshot_path],
                env={"BORG_PASSPHRASE": self.config.get("integration", {}).get("borg_passphrase", "")},
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"Error backing up to borg: {result.stderr}")
                return False
            
            self.logger.info(f"Exported snapshot to borg: {output_path}::{archive_name}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error exporting to borg: {e}")
            return False
    
    def _export_to_duplicity(self, snapshot_path: str, output_path: str) -> bool:
        """Export to duplicity backup."""
        try:
            # Backup to duplicity
            result = subprocess.run(
                ["duplicity", "full", snapshot_path, f"file://{output_path}"],
                env={
                    "PASSPHRASE": self.config.get("integration", {}).get("duplicity_passphrase", "")
                },
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"Error backing up to duplicity: {result.stderr}")
                return False
            
            self.logger.info(f"Exported snapshot to duplicity: {output_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error exporting to duplicity: {e}")
            return False
    
    def import_from_format(self, format_name: str, input_path: str, output_path: str) -> bool:
        """
        Import a backup from a different format.
        
        Args:
            format_name: Source format name
            input_path: Path to the backup to import
            output_path: Path to save the imported snapshot
            
        Returns:
            True if import was successful, False otherwise
        """
        if format_name not in self.SUPPORTED_FORMATS:
            self.logger.error(f"Unsupported import format: {format_name}")
            return False
        
        try:
            # Create output directory if it doesn't exist
            Path(output_path).mkdir(parents=True, exist_ok=True)
            
            if format_name == "tar":
                return self._import_from_tar(input_path, output_path)
            elif format_name == "zip":
                return self._import_from_zip(input_path, output_path)
            elif format_name == "restic":
                return self._import_from_restic(input_path, output_path)
            elif format_name == "borg":
                return self._import_from_borg(input_path, output_path)
            elif format_name == "duplicity":
                return self._import_from_duplicity(input_path, output_path)
            else:
                self.logger.error(f"Import format not implemented: {format_name}")
                return False
        
        except Exception as e:
            self.logger.error(f"Error importing from {format_name}: {e}")
            return False
    
    def _import_from_tar(self, input_path: str, output_path: str) -> bool:
        """Import from tar format."""
        try:
            # Extract tar archive
            result = subprocess.run(
                ["tar", "-xzf", input_path, "-C", output_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"Error extracting tar archive: {result.stderr}")
                return False
            
            self.logger.info(f"Imported from tar: {input_path} to {output_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error importing from tar: {e}")
            return False
    
    def _import_from_zip(self, input_path: str, output_path: str) -> bool:
        """Import from zip format."""
        try:
            # Extract zip archive
            result = subprocess.run(
                ["unzip", input_path, "-d", output_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"Error extracting zip archive: {result.stderr}")
                return False
            
            self.logger.info(f"Imported from zip: {input_path} to {output_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error importing from zip: {e}")
            return False
    
    def _import_from_restic(self, input_path: str, output_path: str) -> bool:
        """Import from restic repository."""
        try:
            # Get latest snapshot ID
            result = subprocess.run(
                ["restic", "snapshots", "--json", "--repo", input_path],
                env={"RESTIC_PASSWORD": self.config.get("integration", {}).get("restic_password", "")},
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"Error listing restic snapshots: {result.stderr}")
                return False
            
            # Parse JSON output to get latest snapshot
            snapshots = json.loads(result.stdout)
            if not snapshots:
                self.logger.error("No restic snapshots found")
                return False
            
            # Sort by time and get the latest
            latest_snapshot = sorted(snapshots, key=lambda s: s["time"])[-1]
            snapshot_id = latest_snapshot["id"]
            
            # Restore from restic repository
            result = subprocess.run(
                ["restic", "restore", snapshot_id, "--target", output_path, "--repo", input_path],
                env={"RESTIC_PASSWORD": self.config.get("integration", {}).get("restic_password", "")},
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"Error restoring from restic: {result.stderr}")
                return False
            
            self.logger.info(f"Imported from restic: {input_path} to {output_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error importing from restic: {e}")
            return False
    
    def _import_from_borg(self, input_path: str, output_path: str) -> bool:
        """Import from borg repository."""
        try:
            # List archives
            result = subprocess.run(
                ["borg", "list", "--json", input_path],
                env={"BORG_PASSPHRASE": self.config.get("integration", {}).get("borg_passphrase", "")},
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"Error listing borg archives: {result.stderr}")
                return False
            
            # Parse JSON output to get latest archive
            archives = json.loads(result.stdout)["archives"]
            if not archives:
                self.logger.error("No borg archives found")
                return False
            
            # Sort by time and get the latest
            latest_archive = sorted(archives, key=lambda a: a["time"])[-1]
            archive_name = latest_archive["name"]
            
            # Extract from borg repository
            result = subprocess.run(
                ["borg", "extract", f"{input_path}::{archive_name}"],
                cwd=output_path,
                env={"BORG_PASSPHRASE": self.config.get("integration", {}).get("borg_passphrase", "")},
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"Error extracting from borg: {result.stderr}")
                return False
            
            self.logger.info(f"Imported from borg: {input_path}::{archive_name} to {output_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error importing from borg: {e}")
            return False
    
    def _import_from_duplicity(self, input_path: str, output_path: str) -> bool:
        """Import from duplicity backup."""
        try:
            # Restore from duplicity
            result = subprocess.run(
                ["duplicity", "restore", f"file://{input_path}", output_path],
                env={
                    "PASSPHRASE": self.config.get("integration", {}).get("duplicity_passphrase", "")
                },
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"Error restoring from duplicity: {result.stderr}")
                return False
            
            self.logger.info(f"Imported from duplicity: {input_path} to {output_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error importing from duplicity: {e}")
            return False