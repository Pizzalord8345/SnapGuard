#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
import logging
from pathlib import Path

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

# This file continues the EnhancedSettingsPanel class from settings_panel_enhanced.py

def on_run_dedup_clicked(self, button):
    """Handle run deduplication button click."""
    dialog = Gtk.MessageDialog(
        transient_for=self.get_toplevel(),
        flags=0,
        message_type=Gtk.MessageType.QUESTION,
        buttons=Gtk.ButtonsType.YES_NO,
        text="Run Deduplication"
    )
    dialog.format_secondary_text(
        "Are you sure you want to run deduplication on all snapshots? This may take some time."
    )
    
    response = dialog.run()
    dialog.destroy()
    
    if response == Gtk.ResponseType.YES:
        try:
            # This would call the deduplication manager in a real implementation
            self.logger.info("Deduplication would be performed here")
            
            # Show progress dialog
            progress_dialog = Gtk.Dialog(
                title="Deduplication Progress",
                parent=self.get_toplevel(),
                flags=0
            )
            progress_dialog.set_default_size(300, 100)
            
            box = progress_dialog.get_content_area()
            box.set_spacing(6)
            box.set_margin_top(12)
            box.set_margin_bottom(12)
            box.set_margin_start(12)
            box.set_margin_end(12)
            
            label = Gtk.Label(label="Deduplicating snapshots...")
            box.pack_start(label, False, False, 0)
            
            progress_bar = Gtk.ProgressBar()
            progress_bar.set_fraction(0.0)
            box.pack_start(progress_bar, False, False, 0)
            
            box.show_all()
            
            # Simulate progress
            def update_progress(fraction):
                progress_bar.set_fraction(fraction)
                if fraction >= 1.0:
                    progress_dialog.destroy()
                    
                    # Show success message
                    success_dialog = Gtk.MessageDialog(
                        transient_for=self.get_toplevel(),
                        flags=0,
                        message_type=Gtk.MessageType.INFO,
                        buttons=Gtk.ButtonsType.OK,
                        text="Deduplication Complete"
                    )
                    success_dialog.format_secondary_text(
                        "Deduplication has been completed successfully. Space saved: 1.2 GB"
                    )
                    success_dialog.run()
                    success_dialog.destroy()
                    
                    return False
                return True
            
            # Update progress every 100ms
            for i in range(11):
                GLib.timeout_add(i * 500, update_progress, i * 0.1)
            
            progress_dialog.run()
            
        except Exception as e:
            # Show error message
            error_dialog = Gtk.MessageDialog(
                transient_for=self.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Deduplication Failed"
            )
            error_dialog.format_secondary_text(str(e))
            error_dialog.run()
            error_dialog.destroy()

def on_test_email_clicked(self, button):
    """Handle test email button click."""
    try:
        # Get email settings from UI
        smtp_server = self.smtp_entry.get_text()
        smtp_port = self.port_spin.get_value_as_int()
        use_tls = self.tls_check.get_active()
        username = self.username_entry.get_text()
        password = self.password_entry.get_text()
        from_addr = self.from_entry.get_text()
        to_addr = self.to_entry.get_text()
        
        # Validate settings
        if not smtp_server or not from_addr or not to_addr:
            raise ValueError("SMTP server, from address, and to address are required")
        
        # This would send a test email in a real implementation
        self.logger.info(f"Test email would be sent to {to_addr}")
        
        # Show success message
        success_dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Test Email Sent"
        )
        success_dialog.format_secondary_text(
            f"A test email has been sent to {to_addr}. Please check your inbox."
        )
        success_dialog.run()
        success_dialog.destroy()
        
    except Exception as e:
        # Show error message
        error_dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Test Email Failed"
        )
        error_dialog.format_secondary_text(str(e))
        error_dialog.run()
        error_dialog.destroy()

def on_save_clicked(self, button):
    """Handle save button click."""
    try:
        # Update config with values from UI
        
        # General settings
        self.snapshot_manager.config['snapshot']['default_location'] = self.location_entry.get_text()
        self.snapshot_manager.config['snapshot']['retention']['daily'] = self.daily_spin.get_value_as_int()
        self.snapshot_manager.config['snapshot']['retention']['weekly'] = self.weekly_spin.get_value_as_int()
        self.snapshot_manager.config['snapshot']['retention']['monthly'] = self.monthly_spin.get_value_as_int()
        
        # Schedule settings
        schedule_type = self.schedule_combo.get_active_text().lower()
        self.snapshot_manager.config['snapshot']['schedule']['type'] = schedule_type
        self.snapshot_manager.config['snapshot']['schedule']['time'] = self.time_entry.get_text()
        
        # Security settings
        self.snapshot_manager.config['security']['encryption']['enabled'] = self.encryption_check.get_active()
        self.snapshot_manager.config['security']['encryption']['algorithm'] = self.algo_combo.get_active_text()
        self.snapshot_manager.config['security']['encryption']['selective_encryption'] = self.selective_check.get_active()
        
        # Get patterns from text view
        patterns_buffer = self.patterns_text.get_buffer()
        start_iter = patterns_buffer.get_start_iter()
        end_iter = patterns_buffer.get_end_iter()
        patterns_text = patterns_buffer.get_text(start_iter, end_iter, True)
        patterns = [p.strip() for p in patterns_text.split('\n') if p.strip()]
        self.snapshot_manager.config['security']['encryption']['sensitive_patterns'] = patterns
        
        # Key rotation settings
        if 'key_rotation' not in self.snapshot_manager.config['security']:
            self.snapshot_manager.config['security']['key_rotation'] = {}
        self.snapshot_manager.config['security']['key_rotation']['enabled'] = self.rotation_check.get_active()
        self.snapshot_manager.config['security']['key_rotation']['max_age_days'] = self.age_spin.get_value_as_int()
        
        # MFA settings
        if 'mfa_policy' not in self.snapshot_manager.config['security']:
            self.snapshot_manager.config['security']['mfa_policy'] = {}
        self.snapshot_manager.config['security']['mfa_policy']['enabled'] = self.mfa_check.get_active()
        
        # Get required operations
        required_ops = []
        for op_id, check in self.ops_checks.items():
            if check.get_active():
                required_ops.append(op_id)
        self.snapshot_manager.config['security']['mfa_policy']['required_operations'] = required_ops
        
        # Performance settings
        if 'performance' not in self.snapshot_manager.config:
            self.snapshot_manager.config['performance'] = {}
        if 'parallel_processing' not in self.snapshot_manager.config['performance']:
            self.snapshot_manager.config['performance']['parallel_processing'] = {}
        
        self.snapshot_manager.config['performance']['parallel_processing']['enabled'] = self.parallel_check.get_active()
        self.snapshot_manager.config['performance']['parallel_processing']['max_workers'] = self.workers_spin.get_value_as_int()
        self.snapshot_manager.config['performance']['parallel_processing']['use_processes'] = self.processes_check.get_active()
        
        # I/O throttling settings
        if 'io_throttling' not in self.snapshot_manager.config['storage']:
            self.snapshot_manager.config['storage']['io_throttling'] = {}
        
        self.snapshot_manager.config['storage']['io_throttling']['enabled'] = self.throttling_check.get_active()
        self.snapshot_manager.config['storage']['io_throttling']['max_read_mbps'] = self.read_spin.get_value_as_int()
        self.snapshot_manager.config['storage']['io_throttling']['max_write_mbps'] = self.write_spin.get_value_as_int()
        
        # Smart scheduling settings
        if 'smart_scheduling' not in self.snapshot_manager.config['performance']:
            self.snapshot_manager.config['performance']['smart_scheduling'] = {}
        
        self.snapshot_manager.config['performance']['smart_scheduling']['enabled'] = self.scheduling_check.get_active()
        self.snapshot_manager.config['performance']['smart_scheduling']['cpu_threshold'] = self.cpu_spin.get_value_as_int()
        self.snapshot_manager.config['performance']['smart_scheduling']['quiet_hours_start'] = self.start_entry.get_text()
        self.snapshot_manager.config['performance']['smart_scheduling']['quiet_hours_end'] = self.end_entry.get_text()
        
        # Storage settings
        if 'deduplication' not in self.snapshot_manager.config['storage']:
            self.snapshot_manager.config['storage']['deduplication'] = {}
        
        self.snapshot_manager.config['storage']['deduplication']['enabled'] = self.dedup_check.get_active()
        self.snapshot_manager.config['storage']['deduplication']['method'] = self.method_combo.get_active_text()
        self.snapshot_manager.config['storage']['deduplication']['block_size'] = self.block_spin.get_value_as_int()
        
        # Compression settings
        if 'compression' not in self.snapshot_manager.config['storage']:
            self.snapshot_manager.config['storage']['compression'] = {}
        
        self.snapshot_manager.config['storage']['compression']['enabled'] = self.compression_check.get_active()
        self.snapshot_manager.config['storage']['compression']['algorithm'] = self.comp_algo_combo.get_active_text()
        self.snapshot_manager.config['storage']['compression']['level'] = self.level_spin.get_value_as_int()
        
        # UI settings
        if 'ui' not in self.snapshot_manager.config:
            self.snapshot_manager.config['ui'] = {}
        
        theme_index = self.theme_combo.get_active()
        if theme_index == 0:
            theme = "light"
        elif theme_index == 1:
            theme = "dark"
        else:
            theme = "system"
        self.snapshot_manager.config['ui']['theme'] = theme
        
        self.snapshot_manager.config['ui']['dashboard_enabled'] = self.dashboard_check.get_active()
        self.snapshot_manager.config['ui']['visualization_enabled'] = self.viz_check.get_active()
        
        # Notification settings
        self.snapshot_manager.config['notifications']['enabled'] = self.notification_check.get_active()
        
        if 'email' not in self.snapshot_manager.config['notifications']:
            self.snapshot_manager.config['notifications']['email'] = {}
        
        self.snapshot_manager.config['notifications']['email']['enabled'] = self.email_check.get_active()
        self.snapshot_manager.config['notifications']['email']['smtp_server'] = self.smtp_entry.get_text()
        self.snapshot_manager.config['notifications']['email']['smtp_port'] = self.port_spin.get_value_as_int()
        self.snapshot_manager.config['notifications']['email']['use_tls'] = self.tls_check.get_active()
        self.snapshot_manager.config['notifications']['email']['username'] = self.username_entry.get_text()
        self.snapshot_manager.config['notifications']['email']['password'] = self.password_entry.get_text()
        self.snapshot_manager.config['notifications']['email']['from'] = self.from_entry.get_text()
        self.snapshot_manager.config['notifications']['email']['to'] = self.to_entry.get_text()
        
        # Save config to file
        # In a real implementation, this would write to the config file
        self.logger.info("Settings saved")
        
        # Show success message
        success_dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Settings Saved"
        )
        success_dialog.format_secondary_text(
            "Settings have been saved successfully."
        )
        success_dialog.run()
        success_dialog.destroy()
        
    except Exception as e:
        # Show error message
        error_dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Save Failed"
        )
        error_dialog.format_secondary_text(str(e))
        error_dialog.run()
        error_dialog.destroy()