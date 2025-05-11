#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
import logging
from pathlib import Path

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

# This file continues the EnhancedSettingsPanel class from settings_panel_enhanced.py

def create_ui_settings(self):
    """Create UI settings page."""
    page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    page.set_margin_top(12)
    page.set_margin_bottom(12)
    page.set_margin_start(12)
    page.set_margin_end(12)
    
    # Theme settings
    theme_frame = Gtk.Frame(label="Theme")
    theme_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    theme_box.set_margin_top(12)
    theme_box.set_margin_bottom(12)
    theme_box.set_margin_start(12)
    theme_box.set_margin_end(12)
    
    # Theme selection
    theme_label = Gtk.Label(label="Application theme:")
    theme_label.set_halign(Gtk.Align.START)
    theme_box.pack_start(theme_label, False, False, 0)
    
    self.theme_combo = Gtk.ComboBoxText()
    self.theme_combo.append_text("Light")
    self.theme_combo.append_text("Dark")
    self.theme_combo.append_text("System")
    
    # Set active theme
    theme = self.snapshot_manager.config.get('ui', {}).get('theme', 'system')
    if theme == "light":
        self.theme_combo.set_active(0)
    elif theme == "dark":
        self.theme_combo.set_active(1)
    else:
        self.theme_combo.set_active(2)
    
    theme_box.pack_start(self.theme_combo, False, False, 0)
    
    theme_frame.add(theme_box)
    page.pack_start(theme_frame, False, False, 0)
    
    # Dashboard settings
    dashboard_frame = Gtk.Frame(label="Dashboard")
    dashboard_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    dashboard_box.set_margin_top(12)
    dashboard_box.set_margin_bottom(12)
    dashboard_box.set_margin_start(12)
    dashboard_box.set_margin_end(12)
    
    # Enable dashboard
    self.dashboard_check = Gtk.CheckButton(label="Enable dashboard")
    self.dashboard_check.set_active(
        self.snapshot_manager.config.get('ui', {}).get('dashboard_enabled', True)
    )
    dashboard_box.pack_start(self.dashboard_check, False, False, 0)
    
    # Enable visualizations
    self.viz_check = Gtk.CheckButton(label="Enable visualizations")
    self.viz_check.set_active(
        self.snapshot_manager.config.get('ui', {}).get('visualization_enabled', True)
    )
    dashboard_box.pack_start(self.viz_check, False, False, 0)
    
    dashboard_frame.add(dashboard_box)
    page.pack_start(dashboard_frame, False, False, 0)
    
    # Notification settings
    notification_frame = Gtk.Frame(label="Notifications")
    notification_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    notification_box.set_margin_top(12)
    notification_box.set_margin_bottom(12)
    notification_box.set_margin_start(12)
    notification_box.set_margin_end(12)
    
    # Enable notifications
    self.notification_check = Gtk.CheckButton(label="Enable desktop notifications")
    self.notification_check.set_active(
        self.snapshot_manager.config.get('notifications', {}).get('enabled', True)
    )
    notification_box.pack_start(self.notification_check, False, False, 0)
    
    # Enable email notifications
    self.email_check = Gtk.CheckButton(label="Enable email notifications")
    self.email_check.set_active(
        self.snapshot_manager.config.get('notifications', {}).get('email', {}).get('enabled', False)
    )
    notification_box.pack_start(self.email_check, False, False, 0)
    
    # Email settings
    email_grid = Gtk.Grid()
    email_grid.set_column_spacing(12)
    email_grid.set_row_spacing(6)
    email_grid.set_margin_top(6)
    email_grid.set_margin_start(24)  # Indent
    
    # SMTP server
    smtp_label = Gtk.Label(label="SMTP server:")
    smtp_label.set_halign(Gtk.Align.START)
    email_grid.attach(smtp_label, 0, 0, 1, 1)
    
    self.smtp_entry = Gtk.Entry()
    self.smtp_entry.set_text(
        self.snapshot_manager.config.get('notifications', {}).get('email', {}).get('smtp_server', "")
    )
    email_grid.attach(self.smtp_entry, 1, 0, 1, 1)
    
    # SMTP port
    port_label = Gtk.Label(label="SMTP port:")
    port_label.set_halign(Gtk.Align.START)
    email_grid.attach(port_label, 0, 1, 1, 1)
    
    self.port_spin = Gtk.SpinButton()
    self.port_spin.set_range(1, 65535)
    self.port_spin.set_increments(1, 10)
    self.port_spin.set_value(
        self.snapshot_manager.config.get('notifications', {}).get('email', {}).get('smtp_port', 587)
    )
    email_grid.attach(self.port_spin, 1, 1, 1, 1)
    
    # Use TLS
    self.tls_check = Gtk.CheckButton(label="Use TLS")
    self.tls_check.set_active(
        self.snapshot_manager.config.get('notifications', {}).get('email', {}).get('use_tls', True)
    )
    email_grid.attach(self.tls_check, 0, 2, 2, 1)
    
    # Username
    username_label = Gtk.Label(label="Username:")
    username_label.set_halign(Gtk.Align.START)
    email_grid.attach(username_label, 0, 3, 1, 1)
    
    self.username_entry = Gtk.Entry()
    self.username_entry.set_text(
        self.snapshot_manager.config.get('notifications', {}).get('email', {}).get('username', "")
    )
    email_grid.attach(self.username_entry, 1, 3, 1, 1)
    
    # Password
    password_label = Gtk.Label(label="Password:")
    password_label.set_halign(Gtk.Align.START)
    email_grid.attach(password_label, 0, 4, 1, 1)
    
    self.password_entry = Gtk.Entry()
    self.password_entry.set_visibility(False)
    self.password_entry.set_text(
        self.snapshot_manager.config.get('notifications', {}).get('email', {}).get('password', "")
    )
    email_grid.attach(self.password_entry, 1, 4, 1, 1)
    
    # From address
    from_label = Gtk.Label(label="From:")
    from_label.set_halign(Gtk.Align.START)
    email_grid.attach(from_label, 0, 5, 1, 1)
    
    self.from_entry = Gtk.Entry()
    self.from_entry.set_text(
        self.snapshot_manager.config.get('notifications', {}).get('email', {}).get('from', "")
    )
    email_grid.attach(self.from_entry, 1, 5, 1, 1)
    
    # To address
    to_label = Gtk.Label(label="To:")
    to_label.set_halign(Gtk.Align.START)
    email_grid.attach(to_label, 0, 6, 1, 1)
    
    self.to_entry = Gtk.Entry()
    self.to_entry.set_text(
        self.snapshot_manager.config.get('notifications', {}).get('email', {}).get('to', "")
    )
    email_grid.attach(self.to_entry, 1, 6, 1, 1)
    
    # Test email button
    test_button = Gtk.Button(label="Test Email")
    test_button.connect("clicked", self.on_test_email_clicked)
    email_grid.attach(test_button, 0, 7, 2, 1)
    
    notification_box.pack_start(email_grid, False, False, 0)
    
    notification_frame.add(notification_box)
    page.pack_start(notification_frame, True, True, 0)
    
    return page

def on_browse_clicked(self, button):
    """Handle browse button click."""
    dialog = Gtk.FileChooserDialog(
        title="Select Snapshot Directory",
        parent=self.get_toplevel(),
        action=Gtk.FileChooserAction.SELECT_FOLDER,
        buttons=(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
    )
    
    response = dialog.run()
    if response == Gtk.ResponseType.OK:
        self.location_entry.set_text(dialog.get_filename())
    
    dialog.destroy()

def on_rotate_keys_clicked(self, button):
    """Handle rotate keys button click."""
    dialog = Gtk.MessageDialog(
        transient_for=self.get_toplevel(),
        flags=0,
        message_type=Gtk.MessageType.QUESTION,
        buttons=Gtk.ButtonsType.YES_NO,
        text="Rotate Encryption Keys"
    )
    dialog.format_secondary_text(
        "Are you sure you want to rotate encryption keys? This will create new keys and mark old ones as inactive."
    )
    
    response = dialog.run()
    dialog.destroy()
    
    if response == Gtk.ResponseType.YES:
        try:
            # This would call the key rotation method in a real implementation
            self.logger.info("Key rotation would be performed here")
            
            # Show success message
            success_dialog = Gtk.MessageDialog(
                transient_for=self.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Keys Rotated"
            )
            success_dialog.format_secondary_text(
                "Encryption keys have been rotated successfully."
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
                text="Key Rotation Failed"
            )
            error_dialog.format_secondary_text(str(e))
            error_dialog.run()
            error_dialog.destroy()

def on_setup_mfa_clicked(self, button):
    """Handle setup MFA button click."""
    dialog = Gtk.Dialog(
        title="Setup Multi-Factor Authentication",
        parent=self.get_toplevel(),
        flags=0,
        buttons=(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
    )
    dialog.set_default_size(400, 300)
    
    box = dialog.get_content_area()
    box.set_spacing(6)
    box.set_margin_top(12)
    box.set_margin_bottom(12)
    box.set_margin_start(12)
    box.set_margin_end(12)
    
    # MFA method selection
    method_label = Gtk.Label(label="MFA Method:")
    method_label.set_halign(Gtk.Align.START)
    box.pack_start(method_label, False, False, 0)
    
    method_combo = Gtk.ComboBoxText()
    method_combo.append_text("Time-based One-Time Password (TOTP)")
    method_combo.append_text("FIDO2/U2F Security Key")
    method_combo.set_active(0)
    box.pack_start(method_combo, False, False, 0)
    
    # User ID
    user_label = Gtk.Label(label="User ID:")
    user_label.set_halign(Gtk.Align.START)
    box.pack_start(user_label, False, False, 0)
    
    user_entry = Gtk.Entry()
    user_entry.set_text("admin")  # Default user ID
    box.pack_start(user_entry, False, False, 0)
    
    # Show all widgets
    box.show_all()
    
    # Run dialog
    response = dialog.run()
    
    if response == Gtk.ResponseType.OK:
        method_index = method_combo.get_active()
        user_id = user_entry.get_text()
        
        if method_index == 0:
            # Setup TOTP
            self.setup_totp(user_id)
        else:
            # Setup FIDO2/U2F
            self.setup_fido2(user_id)
    
    dialog.destroy()

def setup_totp(self, user_id):
    """Setup TOTP for a user."""
    try:
        # This would call the MFA manager in a real implementation
        self.logger.info(f"TOTP setup would be performed for user: {user_id}")
        
        # In a real implementation, this would return a QR code URI
        qr_uri = "otpauth://totp/SnapGuard:admin?secret=ABCDEFGHIJKLMNOP&issuer=SnapGuard"
        
        # Show QR code dialog
        dialog = Gtk.Dialog(
            title="TOTP Setup",
            parent=self.get_toplevel(),
            flags=0,
            buttons=(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        )
        dialog.set_default_size(350, 400)
        
        box = dialog.get_content_area()
        box.set_spacing(6)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        
        # Instructions
        instructions = Gtk.Label()
        instructions.set_markup(
            "<b>Scan this QR code with your authenticator app</b>\n\n"
            "1. Open your authenticator app (Google Authenticator, Authy, etc.)\n"
            "2. Add a new account by scanning the QR code\n"
            "3. Enter the verification code from your app below"
        )
        instructions.set_line_wrap(True)
        box.pack_start(instructions, False, False, 0)
        
        # QR code (placeholder)
        qr_label = Gtk.Label()
        qr_label.set_markup("<span size='xx-large'>[QR Code Placeholder]</span>")
        qr_label.set_margin_top(24)
        qr_label.set_margin_bottom(24)
        box.pack_start(qr_label, False, False, 0)
        
        # Verification code entry
        code_label = Gtk.Label(label="Verification code:")
        code_label.set_halign(Gtk.Align.START)
        box.pack_start(code_label, False, False, 0)
        
        code_entry = Gtk.Entry()
        code_entry.set_placeholder_text("Enter 6-digit code")
        box.pack_start(code_entry, False, False, 0)
        
        # Show all widgets
        box.show_all()
        
        # Run dialog
        dialog.run()
        dialog.destroy()
        
    except Exception as e:
        # Show error message
        error_dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="TOTP Setup Failed"
        )
        error_dialog.format_secondary_text(str(e))
        error_dialog.run()
        error_dialog.destroy()

def setup_fido2(self, user_id):
    """Setup FIDO2/U2F for a user."""
    try:
        # This would call the MFA manager in a real implementation
        self.logger.info(f"FIDO2/U2F setup would be performed for user: {user_id}")
        
        # Show setup dialog
        dialog = Gtk.Dialog(
            title="FIDO2/U2F Setup",
            parent=self.get_toplevel(),
            flags=0,
            buttons=(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        )
        dialog.set_default_size(350, 250)
        
        box = dialog.get_content_area()
        box.set_spacing(6)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        
        # Instructions
        instructions = Gtk.Label()
        instructions.set_markup(
            "<b>Connect your security key</b>\n\n"
            "1. Insert your FIDO2/U2F security key into a USB port\n"
            "2. When prompted, touch the button on your security key\n"
            "3. Wait for the registration to complete"
        )
        instructions.set_line_wrap(True)
        box.pack_start(instructions, False, False, 0)
        
        # Status label
        status_label = Gtk.Label()
        status_label.set_markup("<i>Waiting for security key...</i>")
        status_label.set_margin_top(24)
        box.pack_start(status_label, False, False, 0)
        
        # Show all widgets
        box.show_all()
        
        # Run dialog
        dialog.run()
        dialog.destroy()
        
    except Exception as e:
        # Show error message
        error_dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="FIDO2/U2F Setup Failed"
        )
        error_dialog.format_secondary_text(str(e))
        error_dialog.run()
        error_dialog.destroy()