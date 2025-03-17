#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
import logging
from pathlib import Path

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from ui.snapshot_list import SnapshotListPanel
from ui.live_mode_panel import LiveModePanel
from ui.settings_panel import SettingsPanel

class MainWindow(Gtk.Window):
    """Main application window with header bar and stack for different panels."""
    
    def __init__(self, snapshot_manager):
        super().__init__(title="BetterSync")
        self.logger = logging.getLogger(__name__)
        self.snapshot_manager = snapshot_manager
        
        # Set window properties
        self.set_default_size(900, 600)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Set up header bar
        self.setup_header_bar()
        
        # Set up main content
        self.setup_content()
        
        # Set up status bar
        self.setup_status_bar()
        
        # Set up timer for status updates
        GLib.timeout_add_seconds(5, self.update_status)
    
    def setup_header_bar(self):
        """Create and configure the header bar."""
        header_bar = Gtk.HeaderBar()
        header_bar.set_show_close_button(True)
        header_bar.props.title = "BetterSync"
        
        # Create stack switcher
        self.stack_switcher = Gtk.StackSwitcher()
        header_bar.set_custom_title(self.stack_switcher)
        
        # Add help button
        help_button = Gtk.Button.new_from_icon_name("help-browser-symbolic", Gtk.IconSize.BUTTON)
        help_button.set_tooltip_text("Help")
        help_button.connect("clicked", self.on_help_clicked)
        header_bar.pack_end(help_button)
        
        self.set_titlebar(header_bar)
    
    def setup_content(self):
        """Set up the main content area with stack for panels."""
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
        snapshot_list = SnapshotListPanel(self.snapshot_manager)
        live_mode = LiveModePanel(self.snapshot_manager)
        settings = SettingsPanel(self.snapshot_manager)
        
        # Add panels to stack
        self.stack.add_titled(snapshot_list, "snapshots", "Snapshots")
        self.stack.add_titled(live_mode, "live_mode", "Live Mode")
        self.stack.add_titled(settings, "settings", "Settings")
        
        # Add stack to main box
        main_box.pack_start(self.stack, True, True, 0)
    
    def setup_status_bar(self):
        """Create and configure the status bar."""
        self.status_bar = Gtk.Statusbar()
        self.status_context = self.status_bar.get_context_id("status")
        
        # Create status box
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        # Add snapshot count label
        self.snapshot_count_label = Gtk.Label()
        status_box.pack_start(self.snapshot_count_label, False, False, 10)
        
        # Add disk usage label
        self.disk_usage_label = Gtk.Label()
        status_box.pack_end(self.disk_usage_label, False, False, 10)
        
        # Add status box to status bar
        self.status_bar.add(status_box)
        
        # Add status bar to window
        self.get_child().pack_end(self.status_bar, False, False, 0)
        
        # Initial status update
        self.update_status()
    
    def update_status(self):
        """Update status bar with current snapshot statistics and system information."""
        try:
            # Get snapshot counts
            snapshots = self.snapshot_manager.get_snapshots()
            btrfs_snapshots = [s for s in snapshots if s.type == "btrfs"]
            overlay_snapshots = [s for s in snapshots if s.type == "overlay"]
            
            # Update snapshot count label
            self.snapshot_count_label.set_text(
                f"Snapshots: {len(snapshots)} total "
                f"({len(btrfs_snapshots)} Btrfs, {len(overlay_snapshots)} OverlayFS)"
            )
            
            # Get snapshot storage directory size if available
            snapshot_dir = Path(self.snapshot_manager.config.get('snapshot_directory', '/var/lib/bettersync/snapshots'))
            if snapshot_dir.exists():
                from utils import get_disk_usage, format_size
                usage = get_disk_usage(snapshot_dir)
                if usage:
                    self.disk_usage_label.set_text(
                        f"Snapshot storage: {format_size(usage['used'])} used "
                        f"({usage['percent']}% of {format_size(usage['total'])})"
                    )
                else:
                    self.disk_usage_label.set_text("Snapshot storage: Unknown")
            else:
                self.disk_usage_label.set_text("Snapshot storage: Not available")
        except Exception as e:
            self.logger.error(f"Error updating status: {e}")
        
        # Return True to keep the timer running
        return True
    
    def on_help_clicked(self, button):
        """Show help dialog when help button is clicked."""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="BetterSync Help"
        )
        
        help_text = """
BetterSync is a snapshot management application for Linux.

• Snapshots: Create and manage persistent snapshots of your system
• Live Mode: Test changes in a temporary environment before applying them
• Settings: Configure the application and automatic snapshots

For more information, visit:
https://github.com/yourusername/bettersync
"""
        
        dialog.format_secondary_text(help_text)
        dialog.run()
        dialog.destroy()
