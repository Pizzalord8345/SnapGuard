#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
import logging
from pathlib import Path

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

# Import original settings panel
from ui.settings_panel import SettingsPanel

class EnhancedSettingsPanel(Gtk.Box):
    """
    Enhanced settings panel with additional configuration options.
    """
    
    def __init__(self, snapshot_manager):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.logger = logging.getLogger(__name__)
        self.snapshot_manager = snapshot_manager
        
        # Set padding
        self.set_margin_top(12)
        self.set_margin_bottom(12)
        self.set_margin_start(12)
        self.set_margin_end(12)
        
        # Create notebook for settings categories
        notebook = Gtk.Notebook()
        self.pack_start(notebook, True, True, 0)
        
        # Add general settings page
        general_page = self.create_general_settings()
        notebook.append_page(general_page, Gtk.Label(label="General"))
        
        # Add security settings page
        security_page = self.create_security_settings()
        notebook.append_page(security_page, Gtk.Label(label="Security"))
        
        # Add performance settings page
        performance_page = self.create_performance_settings()
        notebook.append_page(performance_page, Gtk.Label(label="Performance"))
        
        # Add storage settings page
        storage_page = self.create_storage_settings()
        notebook.append_page(storage_page, Gtk.Label(label="Storage"))
        
        # Add UI settings page
        ui_page = self.create_ui_settings()
        notebook.append_page(ui_page, Gtk.Label(label="UI"))
        
        # Add save button
        save_button = Gtk.Button(label="Save Settings")
        save_button.connect("clicked", self.on_save_clicked)
        self.pack_end(save_button, False, False, 0)
    
    def create_general_settings(self):
        """Create general settings page."""
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_margin_top(12)
        page.set_margin_bottom(12)
        page.set_margin_start(12)
        page.set_margin_end(12)
        
        # Snapshot location
        location_frame = Gtk.Frame(label="Snapshot Location")
        location_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        location_box.set_margin_top(12)
        location_box.set_margin_bottom(12)
        location_box.set_margin_start(12)
        location_box.set_margin_end(12)
        
        self.location_entry = Gtk.Entry()
        self.location_entry.set_text(self.snapshot_manager.config['snapshot']['default_location'])
        location_box.pack_start(self.location_entry, True, True, 0)
        
        browse_button = Gtk.Button(label="Browse")
        browse_button.connect("clicked", self.on_browse_clicked)
        location_box.pack_start(browse_button, False, False, 0)
        
        location_frame.add(location_box)
        page.pack_start(location_frame, False, False, 0)
        
        # Retention policy
        retention_frame = Gtk.Frame(label="Retention Policy")
        retention_grid = Gtk.Grid()
        retention_grid.set_column_spacing(12)
        retention_grid.set_row_spacing(6)
        retention_grid.set_margin_top(12)
        retention_grid.set_margin_bottom(12)
        retention_grid.set_margin_start(12)
        retention_grid.set_margin_end(12)
        
        # Daily retention
        daily_label = Gtk.Label(label="Daily snapshots:")
        daily_label.set_halign(Gtk.Align.START)
        retention_grid.attach(daily_label, 0, 0, 1, 1)
        
        self.daily_spin = Gtk.SpinButton()
        self.daily_spin.set_range(1, 30)
        self.daily_spin.set_increments(1, 5)
        self.daily_spin.set_value(self.snapshot_manager.config['snapshot']['retention']['daily'])
        retention_grid.attach(self.daily_spin, 1, 0, 1, 1)
        
        # Weekly retention
        weekly_label = Gtk.Label(label="Weekly snapshots:")
        weekly_label.set_halign(Gtk.Align.START)
        retention_grid.attach(weekly_label, 0, 1, 1, 1)
        
        self.weekly_spin = Gtk.SpinButton()
        self.weekly_spin.set_range(1, 52)
        self.weekly_spin.set_increments(1, 4)
        self.weekly_spin.set_value(self.snapshot_manager.config['snapshot']['retention']['weekly'])
        retention_grid.attach(self.weekly_spin, 1, 1, 1, 1)
        
        # Monthly retention
        monthly_label = Gtk.Label(label="Monthly snapshots:")
        monthly_label.set_halign(Gtk.Align.START)
        retention_grid.attach(monthly_label, 0, 2, 1, 1)
        
        self.monthly_spin = Gtk.SpinButton()
        self.monthly_spin.set_range(1, 60)
        self.monthly_spin.set_increments(1, 6)
        self.monthly_spin.set_value(self.snapshot_manager.config['snapshot']['retention']['monthly'])
        retention_grid.attach(self.monthly_spin, 1, 2, 1, 1)
        
        retention_frame.add(retention_grid)
        page.pack_start(retention_frame, False, False, 0)
        
        # Schedule settings
        schedule_frame = Gtk.Frame(label="Automatic Snapshots")
        schedule_grid = Gtk.Grid()
        schedule_grid.set_column_spacing(12)
        schedule_grid.set_row_spacing(6)
        schedule_grid.set_margin_top(12)
        schedule_grid.set_margin_bottom(12)
        schedule_grid.set_margin_start(12)
        schedule_grid.set_margin_end(12)
        
        # Enable automatic snapshots
        self.auto_check = Gtk.CheckButton(label="Enable automatic snapshots")
        self.auto_check.set_active(True)  # Assume enabled by default
        schedule_grid.attach(self.auto_check, 0, 0, 2, 1)
        
        # Schedule type
        type_label = Gtk.Label(label="Schedule type:")
        type_label.set_halign(Gtk.Align.START)
        schedule_grid.attach(type_label, 0, 1, 1, 1)
        
        self.schedule_combo = Gtk.ComboBoxText()
        self.schedule_combo.append_text("Daily")
        self.schedule_combo.append_text("Weekly")
        self.schedule_combo.append_text("Monthly")
        self.schedule_combo.set_active(0)  # Default to daily
        schedule_grid.attach(self.schedule_combo, 1, 1, 1, 1)
        
        # Schedule time
        time_label = Gtk.Label(label="Time:")
        time_label.set_halign(Gtk.Align.START)
        schedule_grid.attach(time_label, 0, 2, 1, 1)
        
        self.time_entry = Gtk.Entry()
        self.time_entry.set_text(self.snapshot_manager.config['snapshot']['schedule']['time'])
        self.time_entry.set_placeholder_text("HH:MM")
        schedule_grid.attach(self.time_entry, 1, 2, 1, 1)
        
        schedule_frame.add(schedule_grid)
        page.pack_start(schedule_frame, False, False, 0)
        
        return page
    
    def create_security_settings(self):
        """Create security settings page."""
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_margin_top(12)
        page.set_margin_bottom(12)
        page.set_margin_start(12)
        page.set_margin_end(12)
        
        # Encryption settings
        encryption_frame = Gtk.Frame(label="Encryption")
        encryption_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        encryption_box.set_margin_top(12)
        encryption_box.set_margin_bottom(12)
        encryption_box.set_margin_start(12)
        encryption_box.set_margin_end(12)
        
        # Enable encryption
        self.encryption_check = Gtk.CheckButton(label="Enable encryption")
        self.encryption_check.set_active(self.snapshot_manager.config['security']['encryption']['enabled'])
        encryption_box.pack_start(self.encryption_check, False, False, 0)
        
        # Encryption algorithm
        algo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        algo_label = Gtk.Label(label="Algorithm:")
        algo_label.set_halign(Gtk.Align.START)
        algo_box.pack_start(algo_label, False, False, 0)
        
        self.algo_combo = Gtk.ComboBoxText()
        self.algo_combo.append_text("aes-256-gcm")
        self.algo_combo.append_text("chacha20-poly1305")
        
        # Set active algorithm
        if self.snapshot_manager.config['security']['encryption']['algorithm'] == "aes-256-gcm":
            self.algo_combo.set_active(0)
        else:
            self.algo_combo.set_active(1)
        
        algo_box.pack_start(self.algo_combo, True, True, 0)
        encryption_box.pack_start(algo_box, False, False, 0)
        
        # Selective encryption
        self.selective_check = Gtk.CheckButton(label="Enable selective encryption")
        self.selective_check.set_active(
            self.snapshot_manager.config['security']['encryption'].get('selective_encryption', False)
        )
        encryption_box.pack_start(self.selective_check, False, False, 0)
        
        # Sensitive patterns
        patterns_label = Gtk.Label(label="Sensitive file patterns (one per line):")
        patterns_label.set_halign(Gtk.Align.START)
        encryption_box.pack_start(patterns_label, False, False, 0)
        
        patterns_scroll = Gtk.ScrolledWindow()
        patterns_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        patterns_scroll.set_min_content_height(100)
        
        self.patterns_text = Gtk.TextView()
        self.patterns_text.set_wrap_mode(Gtk.WrapMode.WORD)
        
        # Set patterns text
        patterns_buffer = self.patterns_text.get_buffer()
        patterns = self.snapshot_manager.config['security']['encryption'].get('sensitive_patterns', [])
        patterns_buffer.set_text("\n".join(patterns))
        
        patterns_scroll.add(self.patterns_text)
        encryption_box.pack_start(patterns_scroll, True, True, 0)
        
        encryption_frame.add(encryption_box)
        page.pack_start(encryption_frame, True, True, 0)
        
        # Key rotation settings
        rotation_frame = Gtk.Frame(label="Key Rotation")
        rotation_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        rotation_box.set_margin_top(12)
        rotation_box.set_margin_bottom(12)
        rotation_box.set_margin_start(12)
        rotation_box.set_margin_end(12)
        
        # Enable key rotation
        self.rotation_check = Gtk.CheckButton(label="Enable automatic key rotation")
        self.rotation_check.set_active(
            self.snapshot_manager.config.get('security', {}).get('key_rotation', {}).get('enabled', False)
        )
        rotation_box.pack_start(self.rotation_check, False, False, 0)
        
        # Key age
        age_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        age_label = Gtk.Label(label="Maximum key age (days):")
        age_label.set_halign(Gtk.Align.START)
        age_box.pack_start(age_label, False, False, 0)
        
        self.age_spin = Gtk.SpinButton()
        self.age_spin.set_range(30, 365)
        self.age_spin.set_increments(1, 30)
        self.age_spin.set_value(
            self.snapshot_manager.config.get('security', {}).get('key_rotation', {}).get('max_age_days', 90)
        )
        age_box.pack_start(self.age_spin, True, True, 0)
        
        rotation_box.pack_start(age_box, False, False, 0)
        
        # Rotate keys now button
        rotate_button = Gtk.Button(label="Rotate Keys Now")
        rotate_button.connect("clicked", self.on_rotate_keys_clicked)
        rotation_box.pack_start(rotate_button, False, False, 0)
        
        rotation_frame.add(rotation_box)
        page.pack_start(rotation_frame, False, False, 0)
        
        # Multi-factor authentication settings
        mfa_frame = Gtk.Frame(label="Multi-Factor Authentication")
        mfa_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        mfa_box.set_margin_top(12)
        mfa_box.set_margin_bottom(12)
        mfa_box.set_margin_start(12)
        mfa_box.set_margin_end(12)
        
        # Enable MFA
        self.mfa_check = Gtk.CheckButton(label="Enable multi-factor authentication")
        self.mfa_check.set_active(
            self.snapshot_manager.config.get('security', {}).get('mfa_policy', {}).get('enabled', False)
        )
        mfa_box.pack_start(self.mfa_check, False, False, 0)
        
        # Required operations
        ops_label = Gtk.Label(label="Required for operations:")
        ops_label.set_halign(Gtk.Align.START)
        mfa_box.pack_start(ops_label, False, False, 0)
        
        # Create checkboxes for operations
        operations = [
            ("restore_snapshot", "Restore snapshot"),
            ("delete_snapshot", "Delete snapshot"),
            ("export_backup", "Export backup"),
            ("key_rotation", "Key rotation")
        ]
        
        required_ops = self.snapshot_manager.config.get('security', {}).get('mfa_policy', {}).get('required_operations', [])
        
        self.ops_checks = {}
        for op_id, op_label in operations:
            check = Gtk.CheckButton(label=op_label)
            check.set_active(op_id in required_ops)
            mfa_box.pack_start(check, False, False, 0)
            self.ops_checks[op_id] = check
        
        # Setup MFA button
        setup_button = Gtk.Button(label="Setup MFA")
        setup_button.connect("clicked", self.on_setup_mfa_clicked)
        mfa_box.pack_start(setup_button, False, False, 0)
        
        mfa_frame.add(mfa_box)
        page.pack_start(mfa_frame, False, False, 0)
        
        return page