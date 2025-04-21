#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
import logging
import os
from pathlib import Path

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Pango

from utils import show_error_dialog, show_confirmation_dialog, format_size
from ui_utils import create_folder_chooser_dialog

class LiveModePanel(Gtk.Box):
    """Panel for managing and using the live mode functionality."""
    
    def __init__(self, snapshot_manager):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.set_margin_top(10)
        self.set_margin_bottom(10)
        self.set_margin_start(10)
        self.set_margin_end(10)
        
        self.logger = logging.getLogger(__name__)
        self.snapshot_manager = snapshot_manager
        
        # Create UI elements
        self.create_info_area()
        self.create_snapshot_selector()
        self.create_mount_settings()
        self.create_action_buttons()
        
        # Set initial states
        self.refresh()
    
    def create_info_area(self):
        """Creates the information area with description of live mode."""
        info_frame = Gtk.Frame(label="Live Mode Information")
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        info_box.set_margin_top(10)
        info_box.set_margin_bottom(10)
        info_box.set_margin_start(10)
        info_box.set_margin_end(10)
        
        info_text = """
<b>What is Live Mode?</b>

Live Mode allows you to work with a temporary layer on top of your system using OverlayFS.
Any changes made in Live Mode are stored separately and can be either committed or discarded later.

<b>Common use cases:</b>
• Testing software installations without affecting the system
• Trying configuration changes safely
• Creating a temporary development environment

<b>How to use:</b>
1. Select an OverlayFS snapshot
2. Configure a mount point
3. Activate Live Mode
4. Use the system normally - changes will only be visible in the mount point
5. When finished, deactivate Live Mode and choose whether to keep or discard changes
"""
        
        info_label = Gtk.Label()
        info_label.set_markup(info_text)
        info_label.set_line_wrap(True)
        info_label.set_xalign(0)
        info_label.set_yalign(0)
        
        info_box.pack_start(info_label, True, True, 0)
        info_frame.add(info_box)
        
        self.pack_start(info_frame, False, False, 0)
    
    def create_snapshot_selector(self):
        """Creates the area for selecting which snapshot to use in live mode."""
        selector_frame = Gtk.Frame(label="Select Snapshot")
        selector_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        selector_box.set_margin_top(10)
        selector_box.set_margin_bottom(10)
        selector_box.set_margin_start(10)
        selector_box.set_margin_end(10)
        
        # Snapshot list store and combo box
        self.snapshot_store = Gtk.ListStore(str, str)  # id, name
        
        snapshot_combo = Gtk.ComboBox.new_with_model(self.snapshot_store)
        renderer_text = Gtk.CellRendererText()
        snapshot_combo.pack_start(renderer_text, True)
        snapshot_combo.add_attribute(renderer_text, "text", 1)
        snapshot_combo.connect("changed", self.on_snapshot_changed)
        
        # Create new button
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hbox.pack_start(snapshot_combo, True, True, 0)
        
        new_button = Gtk.Button(label="Create New")
        new_button.connect("clicked", self.on_create_new_clicked)
        hbox.pack_start(new_button, False, False, 0)
        
        selector_box.pack_start(hbox, False, False, 0)
        
        # Snapshot details
        self.snapshot_details = Gtk.Label()
        self.snapshot_details.set_markup("<i>No snapshot selected</i>")
        self.snapshot_details.set_xalign(0)
        selector_box.pack_start(self.snapshot_details, False, False, 5)
        
        selector_frame.add(selector_box)
        self.pack_start(selector_frame, False, False, 0)
        
        # Keep a reference to the combo box
        self.snapshot_combo = snapshot_combo
    
    def create_mount_settings(self):
        """Creates the area for configuring mount settings."""
        mount_frame = Gtk.Frame(label="Mount Settings")
        mount_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        mount_box.set_margin_top(10)
        mount_box.set_margin_bottom(10)
        mount_box.set_margin_start(10)
        mount_box.set_margin_end(10)
        
        # Mount point
        mount_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        mount_label = Gtk.Label(label="Mount Point:")
        mount_hbox.pack_start(mount_label, False, False, 0)
        
        self.mount_entry = Gtk.Entry()
        self.mount_entry.set_text("/mnt/livemode")
        mount_hbox.pack_start(self.mount_entry, True, True, 0)
        
        mount_button = Gtk.Button(label="Browse...")
        mount_button.connect("clicked", self.on_mount_browse_clicked)
        mount_hbox.pack_start(mount_button, False, False, 0)
        
        mount_box.pack_start(mount_hbox, False, False, 0)
        
        # Status
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        status_label = Gtk.Label(label="Status:")
        status_box.pack_start(status_label, False, False, 0)
        
        self.status_label = Gtk.Label(label="Inactive")
        self.status_label.set_xalign(0)
        status_box.pack_start(self.status_label, True, True, 0)
        
        mount_box.pack_start(status_box, False, False, 5)
        
        mount_frame.add(mount_box)
        self.pack_start(mount_frame, False, False, 0)
    
    def create_action_buttons(self):
        """Creates the buttons for controlling live mode."""
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        # Activate button
        self.activate_button = Gtk.Button(label="Activate Live Mode")
        self.activate_button.connect("clicked", self.on_activate_clicked)
        self.activate_button.set_sensitive(False)
        button_box.pack_start(self.activate_button, True, True, 0)
        
        # Deactivate button
        self.deactivate_button = Gtk.Button(label="Deactivate Live Mode")
        self.deactivate_button.connect("clicked", self.on_deactivate_clicked)
        self.deactivate_button.set_sensitive(False)
        button_box.pack_start(self.deactivate_button, True, True, 0)
        
        # Commit changes button
        self.commit_button = Gtk.Button(label="Commit Changes")
        self.commit_button.connect("clicked", self.on_commit_clicked)
        self.commit_button.set_sensitive(False)
        button_box.pack_start(self.commit_button, True, True, 0)
        
        self.pack_end(button_box, False, False, 10)
    
    def refresh(self):
        """Refreshes the panel with current data."""
        # Clear previous data
        self.snapshot_store.clear()
        
        # Get overlay snapshots
        snapshots = self.snapshot_manager.get_snapshots("overlay")
        
        # Add to store
        for snapshot in snapshots:
            self.snapshot_store.append([snapshot.id, snapshot.name])
        
        # Find active snapshot
        active_snapshot = None
        active_iter = None
        
        for i, snapshot in enumerate(snapshots):
            if snapshot.is_active:
                active_snapshot = snapshot
                active_iter = self.snapshot_store.get_iter_from_string(str(i))
                break
        
        # Update UI
        if active_snapshot:
            self.snapshot_combo.set_active_iter(active_iter)
            self.update_status("Active", active_snapshot.path)
            
            # Update buttons
            self.activate_button.set_sensitive(False)
            self.deactivate_button.set_sensitive(True)
            self.commit_button.set_sensitive(True)
        else:
            # Reset status
            self.update_status("Inactive")
            
            # Update buttons
            self.activate_button.set_sensitive(len(snapshots) > 0)
            self.deactivate_button.set_sensitive(False)
            self.commit_button.set_sensitive(False)
    
    def update_status(self, status, mount_path=None):
        """Updates the status label with current state."""
        if status == "Active":
            self.status_label.set_markup(f"<span foreground='green'><b>{status}</b></span> - Mounted at {mount_path}")
        else:
            self.status_label.set_markup(f"<span foreground='red'><b>{status}</b></span>")
    
    def on_snapshot_changed(self, combo):
        """Called when a snapshot is selected."""
        tree_iter = combo.get_active_iter()
        if tree_iter is not None:
            model = combo.get_model()
            snapshot_id = model[tree_iter][0]
            snapshot = self.snapshot_manager.get_snapshot_by_id(snapshot_id)
            
            if snapshot:
                # Update details
                created = snapshot.timestamp.split("T")[0]
                self.snapshot_details.set_markup(
                    f"<b>{snapshot.name}</b>\n"
                    f"Created: {created} | Size: {format_size(snapshot.size)}\n"
                    f"Path: {snapshot.path}"
                )
                
                # Update buttons
                self.activate_button.set_sensitive(not snapshot.is_active)
                self.deactivate_button.set_sensitive(snapshot.is_active)
                self.commit_button.set_sensitive(snapshot.is_active)
            else:
                self.snapshot_details.set_markup("<i>Invalid snapshot</i>")
                self.activate_button.set_sensitive(False)
        else:
            self.snapshot_details.set_markup("<i>No snapshot selected</i>")
            self.activate_button.set_sensitive(False)
    
    def on_create_new_clicked(self, button):
        """Creates a new OverlayFS snapshot."""
        dialog = Gtk.Dialog(
            title="Create New OverlayFS Snapshot",
            transient_for=self.get_toplevel(),
            flags=0
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        
        content_area = dialog.get_content_area()
        content_area.set_spacing(6)
        content_area.set_margin_top(10)
        content_area.set_margin_bottom(10)
        content_area.set_margin_start(10)
        content_area.set_margin_end(10)
        
        # Name
        name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        name_label = Gtk.Label(label="Name:")
        name_box.pack_start(name_label, False, False, 0)
        
        name_entry = Gtk.Entry()
        name_entry.set_text("LiveMode_" + GLib.DateTime.new_now_local().format("%Y-%m-%d"))
        name_box.pack_start(name_entry, True, True, 0)
        
        content_area.pack_start(name_box, False, False, 0)
        
        # Source path
        source_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        source_label = Gtk.Label(label="Source Path:")
        source_box.pack_start(source_label, False, False, 0)
        
        source_entry = Gtk.Entry()
        source_entry.set_text("/")
        source_box.pack_start(source_entry, True, True, 0)
        
        source_button = Gtk.Button(label="Browse...")
        source_button.connect("clicked", lambda b: self.on_source_browse_clicked(b, source_entry))
        source_box.pack_start(source_button, False, False, 0)
        
        content_area.pack_start(source_box, False, False, 0)
        
        # Description
        desc_label = Gtk.Label(label="Description:")
        desc_label.set_halign(Gtk.Align.START)
        content_area.pack_start(desc_label, False, False, 0)
        
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_min_content_height(100)
        
        desc_text = Gtk.TextView()
        desc_text.set_wrap_mode(Gtk.WrapMode.WORD)
        
        scrolled_window.add(desc_text)
        content_area.pack_start(scrolled_window, True, True, 0)
        
        dialog.show_all()
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            name = name_entry.get_text()
            source_path = source_entry.get_text()
            
            buffer = desc_text.get_buffer()
            start_iter, end_iter = buffer.get_bounds()
            description = buffer.get_text(start_iter, end_iter, False)
            
            # Create snapshot
            snapshot = self.snapshot_manager.create_overlay_snapshot(name, source_path, description)
            
            if snapshot:
                self.refresh()
                
                # Select the new snapshot
                for i, row in enumerate(self.snapshot_store):
                    if row[0] == snapshot.id:
                        self.snapshot_combo.set_active(i)
                        break
            else:
                show_error_dialog(
                    self.get_toplevel(),
                    "Error creating snapshot",
                    "Check log for details."
                )
        
        dialog.destroy()
        
    def on_source_browse_clicked(self, button, entry):
        """Opens a file chooser for selecting the source path."""
        dialog = create_folder_chooser_dialog(self.get_toplevel(), "Select Source Path")
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            entry.set_text(dialog.get_filename())
        
        dialog.destroy()
    
    def on_mount_browse_clicked(self, button):
        """Opens a file chooser for selecting the mount point."""
        dialog = create_folder_chooser_dialog(self.get_toplevel(), "Select Mount Point")
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.mount_entry.set_text(dialog.get_filename())
        
        dialog.destroy()
    
    def on_activate_clicked(self, button):
        """Activates live mode with the selected snapshot."""
        tree_iter = self.snapshot_combo.get_active_iter()
        if tree_iter is None:
            return
        
        model = self.snapshot_combo.get_model()
        snapshot_id = model[tree_iter][0]
        mount_point = self.mount_entry.get_text()
        
        # Validate mount point
        if not mount_point:
            show_error_dialog(
                self.get_toplevel(),
                "Invalid mount point",
                "Please specify a valid mount point."
            )
            return
        
        # Check if mount point is already used
        if Path(mount_point).exists() and any(os.listdir(mount_point)):
            confirm = show_confirmation_dialog(
                self.get_toplevel(),
                "Mount point is not empty",
                "The mount point already contains files. These will be hidden during live mode. Continue?"
            )
            if not confirm:
                return
        
        # Ensure mount point directory exists
        Path(mount_point).mkdir(parents=True, exist_ok=True)
        
        # Activate live mode
        success = self.snapshot_manager.activate_live_mode(snapshot_id, mount_point)
        
        if success:
            self.refresh()
        else:
            show_error_dialog(
                self.get_toplevel(),
                "Error activating live mode",
                "Please check the application logs for details."
            )
    
    def on_deactivate_clicked(self, button):
        """Deactivates live mode without committing changes."""
        # Get active snapshot
        active_snapshot = None
        for snapshot in self.snapshot_manager.get_snapshots("overlay"):
            if snapshot.is_active:
                active_snapshot = snapshot
                break
        
        if not active_snapshot:
            return
        
        # Confirm
        confirm = show_confirmation_dialog(
            self.get_toplevel(),
            "Deactivate Live Mode?",
            "Any changes made in live mode will be discarded. Continue?"
        )
        
        if not confirm:
            return
        
        # Get mount point
        mount_point = self.mount_entry.get_text()
        
        # Deactivate live mode (commit=False to discard changes)
        success = self.snapshot_manager.deactivate_live_mode(active_snapshot.id, mount_point, False)
        
        if success:
            self.refresh()
        else:
            show_error_dialog(
                self.get_toplevel(),
                "Error deactivating live mode",
                "Please check the application logs for details."
            )
    
    def on_commit_clicked(self, button):
        """Deactivates live mode and commits changes."""
        # Get active snapshot
        active_snapshot = None
        for snapshot in self.snapshot_manager.get_snapshots("overlay"):
            if snapshot.is_active:
                active_snapshot = snapshot
                break
        
        if not active_snapshot:
            return
        
        # Confirm
        confirm = show_confirmation_dialog(
            self.get_toplevel(),
            "Commit changes?",
            "Changes made in live mode will be committed to the snapshot. Continue?"
        )
        
        if not confirm:
            return
        
        # Get mount point
        mount_point = self.mount_entry.get_text()
        
        # Deactivate live mode (commit=True to keep changes)
        success = self.snapshot_manager.deactivate_live_mode(active_snapshot.id, mount_point, True)
        
        if success:
            self.refresh()
        else:
            show_error_dialog(
                self.get_toplevel(),
                "Error committing changes",
                "Please check the application logs for details."
            )
