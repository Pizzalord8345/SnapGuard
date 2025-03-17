#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
import logging
from pathlib import Path

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Pango

from utils import show_error_dialog, show_confirmation_dialog, format_size

class SettingsPanel(Gtk.Box):
    """Panel for configuring BetterSync application settings."""
    
    def __init__(self, snapshot_manager, parent_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.logger = logging.getLogger(__name__)
        self.snapshot_manager = snapshot_manager
        self.parent_window = parent_window
        
        # Create UI elements
        self.create_widgets()
        
        # Load initial settings
        self.load_settings()
    
    def create_widgets(self):
        """Creates the UI elements."""
        # Haupt-Container mit Padding
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_margin_top(12)
        main_box.set_margin_bottom(12)
        main_box.set_margin_start(12)
        main_box.set_margin_end(12)
        self.pack_start(main_box, True, True, 0)
        
        # Allgemeine Einstellungen
        general_frame = Gtk.Frame(label="General Settings")
        main_box.pack_start(general_frame, False, False, 0)
        
        general_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        general_box.set_margin_top(12)
        general_box.set_margin_bottom(12)
        general_box.set_margin_start(12)
        general_box.set_margin_end(12)
        general_frame.add(general_box)
        
        # Snapshot-Verzeichnis
        snapshot_dir_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        general_box.pack_start(snapshot_dir_box, False, False, 0)
        
        snapshot_dir_label = Gtk.Label(label="Snapshot directory:")
        snapshot_dir_label.set_halign(Gtk.Align.START)
        snapshot_dir_box.pack_start(snapshot_dir_label, False, False, 0)
        
        self.snapshot_dir_entry = Gtk.Entry()
        self.snapshot_dir_entry.set_hexpand(True)
        snapshot_dir_box.pack_start(self.snapshot_dir_entry, True, True, 0)
        
        snapshot_dir_button = Gtk.Button(label="Browse...")
        snapshot_dir_button.connect("clicked", self.on_browse_snapshot_dir_clicked)
        snapshot_dir_box.pack_start(snapshot_dir_button, False, False, 0)
        
        # Maximale Anzahl an Snapshots
        max_snapshots_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        general_box.pack_start(max_snapshots_box, False, False, 0)
        
        max_snapshots_label = Gtk.Label(label="Maximum number of snapshots:")
        max_snapshots_label.set_halign(Gtk.Align.START)
        max_snapshots_box.pack_start(max_snapshots_label, False, False, 0)
        
        self.max_snapshots_spin = Gtk.SpinButton()
        self.max_snapshots_spin.set_range(1, 100)
        self.max_snapshots_spin.set_increments(1, 5)
        max_snapshots_box.pack_start(self.max_snapshots_spin, True, True, 0)
        
        # OverlayFS-Einstellungen
        overlay_frame = Gtk.Frame(label="OverlayFS Settings")
        main_box.pack_start(overlay_frame, False, False, 0)
        
        overlay_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        overlay_box.set_margin_top(12)
        overlay_box.set_margin_bottom(12)
        overlay_box.set_margin_start(12)
        overlay_box.set_margin_end(12)
        overlay_frame.add(overlay_box)
        
        # Standard-Mount-Punkt
        overlay_mount_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        overlay_box.pack_start(overlay_mount_box, False, False, 0)
        
        overlay_mount_label = Gtk.Label(label="Default mount point:")
        overlay_mount_label.set_halign(Gtk.Align.START)
        overlay_mount_box.pack_start(overlay_mount_label, False, False, 0)
        
        self.overlay_mount_entry = Gtk.Entry()
        self.overlay_mount_entry.set_hexpand(True)
        overlay_mount_box.pack_start(self.overlay_mount_entry, True, True, 0)
        
        overlay_mount_button = Gtk.Button(label="Browse...")
        overlay_mount_button.connect("clicked", self.on_browse_overlay_mount_clicked)
        overlay_mount_box.pack_start(overlay_mount_button, False, False, 0)
        
        # Btrfs-Einstellungen
        btrfs_frame = Gtk.Frame(label="Btrfs Settings")
        main_box.pack_start(btrfs_frame, False, False, 0)
        
        btrfs_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        btrfs_box.set_margin_top(12)
        btrfs_box.set_margin_bottom(12)
        btrfs_box.set_margin_start(12)
        btrfs_box.set_margin_end(12)
        btrfs_frame.add(btrfs_box)
        
        # Standard-Mount-Punkt
        btrfs_mount_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        btrfs_box.pack_start(btrfs_mount_box, False, False, 0)
        
        btrfs_mount_label = Gtk.Label(label="Default mount point:")
        btrfs_mount_label.set_halign(Gtk.Align.START)
        btrfs_mount_box.pack_start(btrfs_mount_label, False, False, 0)
        
        self.btrfs_mount_entry = Gtk.Entry()
        self.btrfs_mount_entry.set_hexpand(True)
        btrfs_mount_box.pack_start(self.btrfs_mount_entry, True, True, 0)
        
        btrfs_mount_button = Gtk.Button(label="Browse...")
        btrfs_mount_button.connect("clicked", self.on_browse_btrfs_mount_clicked)
        btrfs_mount_box.pack_start(btrfs_mount_button, False, False, 0)
        
        # Automatische Snapshots
        auto_frame = Gtk.Frame(label="Automatic Snapshots")
        main_box.pack_start(auto_frame, False, False, 0)
        
        auto_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        auto_box.set_margin_top(12)
        auto_box.set_margin_bottom(12)
        auto_box.set_margin_start(12)
        auto_box.set_margin_end(12)
        auto_frame.add(auto_box)
        
        # Aktivieren/Deaktivieren
        self.auto_snapshot_switch = Gtk.Switch()
        self.auto_snapshot_switch.set_halign(Gtk.Align.START)
        
        auto_snapshot_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        auto_box.pack_start(auto_snapshot_box, False, False, 0)
        
        auto_snapshot_label = Gtk.Label(label="Enable automatic snapshots:")
        auto_snapshot_label.set_halign(Gtk.Align.START)
        auto_snapshot_box.pack_start(auto_snapshot_label, False, False, 0)
        
        auto_snapshot_box.pack_end(self.auto_snapshot_switch, False, False, 0)
        
        # Speichern/Zurücksetzen-Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_margin_top(12)
        main_box.pack_end(button_box, False, False, 0)
        
        reset_button = Gtk.Button(label="Reset to Default")
        reset_button.connect("clicked", self.on_reset_clicked)
        button_box.pack_start(reset_button, True, True, 0)
        
        save_button = Gtk.Button(label="Save Settings")
        save_button.connect("clicked", self.on_save_clicked)
        button_box.pack_end(save_button, True, True, 0)
        
        # Bereinigung-Button
        cleanup_button = Gtk.Button(label="Clean up old snapshots")
        cleanup_button.connect("clicked", self.on_cleanup_clicked)
        main_box.pack_end(cleanup_button, False, False, 0)
    
    def load_settings(self):
        """Loads settings from config into UI elements."""
        config = self.snapshot_manager.config
        
        # Allgemeine Einstellungen
        self.snapshot_dir_entry.set_text(config.get('snapshot_directory', '/var/lib/bettersync/snapshots'))
        self.max_snapshots_spin.set_value(config.get('max_snapshots', 10))
        
        # OverlayFS-Einstellungen
        self.overlay_mount_entry.set_text(config.get('overlay_mount_point', '/mnt/overlay'))
        
        # Btrfs-Einstellungen
        self.btrfs_mount_entry.set_text(config.get('btrfs_mount_point', '/mnt/btrfs'))
        
        # Automatische Snapshots
        self.auto_snapshot_switch.set_active(config.get('auto_snapshot_enabled', True))
    
    def on_browse_snapshot_dir_clicked(self, button):
        """Handler für den 'Browse'-Button des Snapshot-Verzeichnisses."""
        dialog = Gtk.FileChooserDialog(
            title="Select Snapshot Directory",
            parent=self.parent_window,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.snapshot_dir_entry.set_text(dialog.get_filename())
        
        dialog.destroy()
    
    def on_browse_overlay_mount_clicked(self, button):
        """Handler für den 'Browse'-Button des OverlayFS-Mount-Punkts."""
        dialog = Gtk.FileChooserDialog(
            title="Select OverlayFS Mount Point",
            parent=self.parent_window,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.overlay_mount_entry.set_text(dialog.get_filename())
        
        dialog.destroy()
    
    def on_browse_btrfs_mount_clicked(self, button):
        """Handler für den 'Browse'-Button des Btrfs-Mount-Punkts."""
        dialog = Gtk.FileChooserDialog(
            title="Select Btrfs Mount Point",
            parent=self.parent_window,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.btrfs_mount_entry.set_text(dialog.get_filename())
        
        dialog.destroy()
    
    def on_reset_clicked(self, button):
        """Handler für den 'Reset to Default'-Button."""
        # Einstellungen neu laden
        self.load_settings()
        
        self.parent_window.show_message("Settings reset to default")
    
    def on_save_clicked(self, button):
        """Handler für den 'Save Settings'-Button."""
        # Werte aus den Eingabefeldern holen
        snapshot_directory = self.snapshot_dir_entry.get_text()
        max_snapshots = self.max_snapshots_spin.get_value_as_int()
        overlay_mount_point = self.overlay_mount_entry.get_text()
        btrfs_mount_point = self.btrfs_mount_entry.get_text()
        auto_snapshot_enabled = self.auto_snapshot_switch.get_active()
        
        # Validierung
        if not snapshot_directory:
            show_error_dialog(
                self.parent_window,
                "Invalid snapshot directory",
                "Please enter a valid snapshot directory."
            )
            return
        
        if not overlay_mount_point:
            show_error_dialog(
                self.parent_window,
                "Invalid OverlayFS mount point",
                "Please enter a valid OverlayFS mount point."
            )
            return
        
        if not btrfs_mount_point:
            show_error_dialog(
                self.parent_window,
                "Invalid Btrfs mount point",
                "Please enter a valid Btrfs mount point."
            )
            return
        
        # Konfiguration aktualisieren
        config = self.snapshot_manager.config
        config['snapshot_directory'] = snapshot_directory
        config['max_snapshots'] = max_snapshots
        config['overlay_mount_point'] = overlay_mount_point
        config['btrfs_mount_point'] = btrfs_mount_point
        config['auto_snapshot_enabled'] = auto_snapshot_enabled
        
        # Konfiguration speichern
        self.snapshot_manager.save_config()
        
        # Automatische Snapshots einrichten oder deaktivieren
        try:
            self.snapshot_manager.setup_automatic_snapshots(auto_snapshot_enabled)
            self.parent_window.show_message("Settings saved")
        except Exception as e:
            self.logger.error(f"Error setting up automatic snapshots: {e}")
            show_error_dialog(
                self.parent_window,
                "Error setting up automatic snapshots",
                str(e)
            )
    
    def on_cleanup_clicked(self, button):
        """Handler für den 'Clean up old snapshots'-Button."""
        max_snapshots = self.max_snapshots_spin.get_value_as_int()
        
        # Bestätigung
        confirm = show_confirmation_dialog(
            self.parent_window,
            "Clean up old snapshots?",
            f"Only the most recent {max_snapshots} snapshots of each type will be kept. This action cannot be undone."
        )
        
        if confirm:
            # Alte Snapshots bereinigen
            deleted_count = self.snapshot_manager.cleanup_old_snapshots(max_snapshots)
            
            self.parent_window.snapshot_list.refresh()
            self.parent_window.update_status()
            
            if deleted_count > 0:
                self.parent_window.show_message(f"{deleted_count} old snapshots were cleaned up")
            else:
                self.parent_window.show_message("No old snapshots to clean up")
