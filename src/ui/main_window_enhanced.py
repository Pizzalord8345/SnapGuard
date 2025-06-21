#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
import logging
from pathlib import Path

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

# Import original UI components
from ui.main_window import MainWindow
from ui.snapshot_list import SnapshotListPanel
from ui.live_mode_panel import LiveModePanel
from ui.settings_panel import SettingsPanel

# Import new UI components
from ui.dashboard import DashboardPanel
from ui.dark_theme import ThemeManager, DarkThemeProvider, create_theme_switcher

class EnhancedMainWindow(MainWindow):
    """
    Enhanced main application window with additional features.
    Extends the original MainWindow class with new capabilities.
    """
    
    def __init__(self, snapshot_manager):
        # Initialize with parent constructor but don't call setup methods yet
        Gtk.Window.__init__(self, title="SnapGuard")
        self.logger = logging.getLogger(__name__)
        self.snapshot_manager = snapshot_manager
        
        # Initialize theme manager
        self.theme_manager = ThemeManager()
        
        # Set window properties
        self.set_default_size(1000, 700)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Set up header bar with enhanced features
        self.setup_enhanced_header_bar()
        
        # Set up main content with enhanced features
        self.setup_enhanced_content()
        
        # Set up status bar
        self.setup_status_bar()
        
        # Apply theme based on settings
        self.apply_theme()
        
        # Set up timer for status updates
        GLib.timeout_add_seconds(5, self.update_status)
    
    def setup_enhanced_header_bar(self):
        """Create and configure the enhanced header bar."""
        header_bar = Gtk.HeaderBar()
        header_bar.set_show_close_button(True)
        header_bar.props.title = "SnapGuard"
        
        # Create stack switcher
        self.stack_switcher = Gtk.StackSwitcher()
        header_bar.set_custom_title(self.stack_switcher)
        
        # Add theme toggle button
        theme_button = Gtk.Button.new_from_icon_name("weather-clear-night-symbolic", Gtk.IconSize.BUTTON)
        theme_button.set_tooltip_text("Toggle Dark Mode")
        theme_button.connect("clicked", self.on_theme_toggle_clicked)
        header_bar.pack_end(theme_button)
        
        # Add help button
        help_button = Gtk.Button.new_from_icon_name("help-browser-symbolic", Gtk.IconSize.BUTTON)
        help_button.set_tooltip_text("Help")
        help_button.connect("clicked", self.on_help_clicked)
        header_bar.pack_end(help_button)
        
        # Add settings button
        settings_button = Gtk.Button.new_from_icon_name("preferences-system-symbolic", Gtk.IconSize.BUTTON)
        settings_button.set_tooltip_text("Settings")
        settings_button.connect("clicked", self.on_settings_clicked)
        header_bar.pack_end(settings_button)
        
        self.set_titlebar(header_bar)
    
    def setup_enhanced_content(self):
        """Set up the main content area with enhanced stack for panels."""
        # Create main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_box)
        
        # Create stack for panels
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(300)
        
        # Connect stack to switcher
        self.stack_switcher.set_stack(self.stack)
        
        # Create panels
        dashboard = DashboardPanel(self.snapshot_manager)
        snapshot_list = SnapshotListPanel(self.snapshot_manager)
        live_mode = LiveModePanel(self.snapshot_manager)
        settings = SettingsPanel(self.snapshot_manager)
        
        # Add panels to stack
        self.stack.add_titled(dashboard, "dashboard", "Dashboard")
        self.stack.add_titled(snapshot_list, "snapshots", "Snapshots")
        self.stack.add_titled(live_mode, "live_mode", "Live Mode")
        self.stack.add_titled(settings, "settings", "Settings")
        
        # Add stack to main box
        main_box.pack_start(self.stack, True, True, 0)
    
    def apply_theme(self):
        """Apply the current theme to the application."""
        # Get theme from settings
        theme = self.snapshot_manager.config.get("ui", {}).get("theme", "system")
        self.theme_manager.set_theme(theme)
        
        # Apply CSS if using dark theme
        if self.theme_manager.is_dark_theme():
            DarkThemeProvider.apply_css_to_widget(self)
    
    def on_theme_toggle_clicked(self, button):
        """Handle theme toggle button click."""
        new_theme = self.theme_manager.toggle_theme()
        self.logger.info(f"Theme changed to: {new_theme}")
        
        # Apply CSS if using dark theme
        if self.theme_manager.is_dark_theme():
            DarkThemeProvider.apply_css_to_widget(self)
        
        # Update config
        self.snapshot_manager.config["ui"]["theme"] = new_theme
        # In a real application, you would save the config here
    
    def on_settings_clicked(self, button):
        """Handle settings button click."""
        # Switch to settings panel
        self.stack.set_visible_child_name("settings")
    
    def on_help_clicked(self, button):
        """Show enhanced help dialog when help button is clicked."""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="SnapGuard Help"
        )
        
        help_text = """
SnapGuard is a modern snapshot management application for Linux.

• Dashboard: View snapshot statistics and system health
• Snapshots: Create and manage persistent snapshots of your system
• Live Mode: Test changes in a temporary environment before applying them
• Settings: Configure the application and automatic snapshots

New Features:
• Enhanced security with key rotation and MFA
• Performance optimizations with parallel processing
• File-level restoration and bootable recovery
• Deduplication for efficient storage usage
• Dark mode and improved UI

For more information, visit:
https://github.com/Pizzalord8345/SnapGuard
"""
        
        dialog.format_secondary_text(help_text)
        dialog.run()
        dialog.destroy()
    
    def create_snapshot_dialog(self):
        """Show enhanced create snapshot dialog with new options."""
        dialog = Gtk.Dialog(
            title="Create Snapshot",
            parent=self,
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
        
        # Description field
        desc_label = Gtk.Label(label="Description:")
        desc_label.set_halign(Gtk.Align.START)
        box.pack_start(desc_label, False, False, 0)
        
        desc_entry = Gtk.Entry()
        desc_entry.set_placeholder_text("Enter snapshot description")
        box.pack_start(desc_entry, False, False, 0)
        
        # Encryption option
        encrypt_check = Gtk.CheckButton(label="Encrypt snapshot")
        encrypt_check.set_active(True)
        box.pack_start(encrypt_check, False, False, 0)
        
        # Deduplication option
        dedup_check = Gtk.CheckButton(label="Deduplicate snapshot")
        dedup_check.set_active(True)
        box.pack_start(dedup_check, False, False, 0)
        
        # Show all widgets
        box.show_all()
        
        # Run dialog
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            description = desc_entry.get_text()
            encrypt = encrypt_check.get_active()
            deduplicate = dedup_check.get_active()
            
            # Create snapshot with enhanced options
            success = self.snapshot_manager.create_snapshot(
                description=description,
                encrypt=encrypt,
                deduplicate=deduplicate
            )
            
            if success:
                self.show_message_dialog("Success", "Snapshot created successfully")
            else:
                self.show_message_dialog("Error", "Failed to create snapshot", Gtk.MessageType.ERROR)
        
        dialog.destroy()
    
    def show_message_dialog(self, title, message, message_type=Gtk.MessageType.INFO):
        """Show a message dialog."""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=message_type,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def restore_file_dialog(self):
        """Show dialog for restoring individual files."""
        dialog = Gtk.Dialog(
            title="Restore File",
            parent=self,
            flags=0,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK, Gtk.ResponseType.OK
            )
        )
        dialog.set_default_size(500, 400)
        
        box = dialog.get_content_area()
        box.set_spacing(6)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        
        # Snapshot selection
        snapshot_label = Gtk.Label(label="Select Snapshot:")
        snapshot_label.set_halign(Gtk.Align.START)
        box.pack_start(snapshot_label, False, False, 0)
        
        snapshot_combo = Gtk.ComboBoxText()
        snapshots = self.snapshot_manager.list_snapshots()
        for snapshot in snapshots:
            snapshot_combo.append_text(snapshot['name'])
        if snapshots:
            snapshot_combo.set_active(0)
        box.pack_start(snapshot_combo, False, False, 0)
        
        # File path entry
        file_label = Gtk.Label(label="File Path:")
        file_label.set_halign(Gtk.Align.START)
        box.pack_start(file_label, False, False, 0)
        
        file_entry = Gtk.Entry()
        file_entry.set_placeholder_text("Enter path to file within snapshot")
        box.pack_start(file_entry, False, False, 0)
        
        # Target path entry
        target_label = Gtk.Label(label="Target Path (optional):")
        target_label.set_halign(Gtk.Align.START)
        box.pack_start(target_label, False, False, 0)
        
        target_entry = Gtk.Entry()
        target_entry.set_placeholder_text("Leave empty to restore to original location")
        box.pack_start(target_entry, False, False, 0)
        
        # Show all widgets
        box.show_all()
        
        # Run dialog
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            snapshot_name = snapshot_combo.get_active_text()
            file_path = file_entry.get_text()
            target_path = target_entry.get_text() or None
            
            if snapshot_name and file_path:
                # Restore file
                success = self.snapshot_manager.restore_file(
                    snapshot_name=snapshot_name,
                    file_path=file_path,
                    target_path=target_path
                )
                
                if success:
                    self.show_message_dialog("Success", "File restored successfully")
                else:
                    self.show_message_dialog("Error", "Failed to restore file", Gtk.MessageType.ERROR)
            else:
                self.show_message_dialog("Error", "Please select a snapshot and enter a file path", Gtk.MessageType.ERROR)
        
        dialog.destroy()
    
    def create_bootable_recovery_dialog(self):
        """Show dialog for creating bootable recovery media."""
        dialog = Gtk.Dialog(
            title="Create Bootable Recovery",
            parent=self,
            flags=0,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK, Gtk.ResponseType.OK
            )
        )
        dialog.set_default_size(400, 200)
        
        box = dialog.get_content_area()
        box.set_spacing(6)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        
        # Snapshot selection
        snapshot_label = Gtk.Label(label="Select Snapshot:")
        snapshot_label.set_halign(Gtk.Align.START)
        box.pack_start(snapshot_label, False, False, 0)
        
        snapshot_combo = Gtk.ComboBoxText()
        snapshots = self.snapshot_manager.list_snapshots()
        for snapshot in snapshots:
            snapshot_combo.append_text(snapshot['name'])
        if snapshots:
            snapshot_combo.set_active(0)
        box.pack_start(snapshot_combo, False, False, 0)
        
        # Device path entry
        device_label = Gtk.Label(label="Target Device:")
        device_label.set_halign(Gtk.Align.START)
        box.pack_start(device_label, False, False, 0)
        
        device_entry = Gtk.Entry()
        device_entry.set_placeholder_text("Enter device path (e.g., /dev/sdb)")
        box.pack_start(device_entry, False, False, 0)
        
        # Warning label
        warning_label = Gtk.Label()
        warning_label.set_markup("<span foreground='red'>Warning: All data on the target device will be erased!</span>")
        box.pack_start(warning_label, False, False, 0)
        
        # Show all widgets
        box.show_all()
        
        # Run dialog
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            snapshot_name = snapshot_combo.get_active_text()
            device_path = device_entry.get_text()
            
            if snapshot_name and device_path:
                # Create bootable recovery
                success = self.snapshot_manager.create_bootable_recovery(
                    snapshot_name=snapshot_name,
                    target_device=device_path
                )
                
                if success:
                    self.show_message_dialog("Success", "Bootable recovery media created successfully")
                else:
                    self.show_message_dialog("Error", "Failed to create bootable recovery media", Gtk.MessageType.ERROR)
            else:
                self.show_message_dialog("Error", "Please select a snapshot and enter a device path", Gtk.MessageType.ERROR)
        
        dialog.destroy()