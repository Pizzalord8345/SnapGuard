#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
import os
import json
import datetime
import threading
import time
from pathlib import Path

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk, Pango

class DashboardPanel(Gtk.Box):
    """
    Dashboard panel showing snapshot statistics and system information.
    """
    
    def __init__(self, snapshot_manager):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.snapshot_manager = snapshot_manager
        
        # Set padding
        self.set_margin_top(12)
        self.set_margin_bottom(12)
        self.set_margin_start(12)
        self.set_margin_end(12)
        
        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.pack_start(scrolled, True, True, 0)
        
        # Create main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        main_box.set_margin_top(12)
        main_box.set_margin_bottom(12)
        main_box.set_margin_start(12)
        main_box.set_margin_end(12)
        scrolled.add(main_box)
        
        # Add header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        header_label = Gtk.Label(label="Dashboard")
        header_label.set_markup("<span size='x-large' weight='bold'>Dashboard</span>")
        header_label.set_halign(Gtk.Align.START)
        header.pack_start(header_label, True, True, 0)
        
        # Add refresh button
        refresh_button = Gtk.Button.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.BUTTON)
        refresh_button.set_tooltip_text("Refresh Dashboard")
        refresh_button.connect("clicked", self.on_refresh_clicked)
        header.pack_end(refresh_button, False, False, 0)
        
        main_box.pack_start(header, False, False, 0)
        
        # Add statistics cards
        stats_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        stats_box.set_homogeneous(True)
        
        # Total snapshots card
        self.total_snapshots_card = self.create_stat_card(
            "Total Snapshots", "0", "All snapshots", "drive-harddisk-symbolic"
        )
        stats_box.pack_start(self.total_snapshots_card, True, True, 0)
        
        # Storage usage card
        self.storage_card = self.create_stat_card(
            "Storage Used", "0 MB", "Snapshot storage", "drive-harddisk-symbolic"
        )
        stats_box.pack_start(self.storage_card, True, True, 0)
        
        # Space saved card
        self.space_saved_card = self.create_stat_card(
            "Space Saved", "0 MB", "Through deduplication", "emblem-default-symbolic"
        )
        stats_box.pack_start(self.space_saved_card, True, True, 0)
        
        main_box.pack_start(stats_box, False, False, 0)
        
        # Add snapshot type distribution
        snapshot_types_frame = Gtk.Frame(label="Snapshot Distribution")
        snapshot_types_frame.set_shadow_type(Gtk.ShadowType.NONE)
        snapshot_types_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        snapshot_types_box.set_margin_top(12)
        snapshot_types_box.set_margin_bottom(12)
        snapshot_types_box.set_margin_start(12)
        snapshot_types_box.set_margin_end(12)
        
        # Create progress bars for snapshot types
        self.btrfs_progress = Gtk.ProgressBar()
        self.btrfs_progress.set_text("BtrFS: 0")
        self.btrfs_progress.set_show_text(True)
        snapshot_types_box.pack_start(self.btrfs_progress, False, False, 0)
        
        self.overlay_progress = Gtk.ProgressBar()
        self.overlay_progress.set_text("OverlayFS: 0")
        self.overlay_progress.set_show_text(True)
        snapshot_types_box.pack_start(self.overlay_progress, False, False, 0)
        
        snapshot_types_frame.add(snapshot_types_box)
        main_box.pack_start(snapshot_types_frame, False, False, 0)
        
        # Add recent snapshots list
        recent_frame = Gtk.Frame(label="Recent Snapshots")
        recent_frame.set_shadow_type(Gtk.ShadowType.NONE)
        
        self.recent_list = Gtk.ListBox()
        self.recent_list.set_selection_mode(Gtk.SelectionMode.NONE)
        
        recent_scrolled = Gtk.ScrolledWindow()
        recent_scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        recent_scrolled.set_min_content_height(200)
        recent_scrolled.add(self.recent_list)
        
        recent_frame.add(recent_scrolled)
        main_box.pack_start(recent_frame, True, True, 0)
        
        # Add system health status
        health_frame = Gtk.Frame(label="System Health")
        health_frame.set_shadow_type(Gtk.ShadowType.NONE)
        health_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        health_box.set_margin_top(12)
        health_box.set_margin_bottom(12)
        health_box.set_margin_start(12)
        health_box.set_margin_end(12)
        
        # Create health indicators
        self.disk_health = self.create_health_indicator("Disk Space", "Unknown")
        health_box.pack_start(self.disk_health, False, False, 0)
        
        self.snapshot_health = self.create_health_indicator("Snapshot Integrity", "Unknown")
        health_box.pack_start(self.snapshot_health, False, False, 0)
        
        self.backup_health = self.create_health_indicator("Backup Status", "Unknown")
        health_box.pack_start(self.backup_health, False, False, 0)
        
        health_frame.add(health_box)
        main_box.pack_start(health_frame, False, False, 0)
        
        # Start background update thread
        self.update_thread = threading.Thread(target=self.background_update, daemon=True)
        self.update_thread.start()
        
        # Initial update
        self.update_dashboard()
    
    def create_stat_card(self, title, value, subtitle, icon_name):
        """Create a statistics card widget."""
        card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        card.get_style_context().add_class("dashboard-card")
        
        # Add icon
        icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.DIALOG)
        card.pack_start(icon, False, False, 0)
        
        # Add text content
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        title_label = Gtk.Label(label=title)
        title_label.set_halign(Gtk.Align.START)
        title_label.get_style_context().add_class("dashboard-title")
        content.pack_start(title_label, False, False, 0)
        
        value_label = Gtk.Label(label=value)
        value_label.set_halign(Gtk.Align.START)
        value_label.get_style_context().add_class("dashboard-value")
        content.pack_start(value_label, False, False, 0)
        
        subtitle_label = Gtk.Label(label=subtitle)
        subtitle_label.set_halign(Gtk.Align.START)
        subtitle_label.get_style_context().add_class("dashboard-subtitle")
        content.pack_start(subtitle_label, False, False, 0)
        
        card.pack_start(content, True, True, 0)
        
        return card
    
    def create_health_indicator(self, name, status):
        """Create a health indicator widget."""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        name_label = Gtk.Label(label=name)
        name_label.set_halign(Gtk.Align.START)
        box.pack_start(name_label, True, True, 0)
        
        status_label = Gtk.Label(label=status)
        box.pack_end(status_label, False, False, 0)
        
        return box
    
    def create_snapshot_row(self, snapshot):
        """Create a row for the recent snapshots list."""
        row = Gtk.ListBoxRow()
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(6)
        box.set_margin_end(6)
        
        # Add snapshot name
        name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        if snapshot.type == "btrfs":
            icon = Gtk.Image.new_from_icon_name("drive-harddisk-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        else:
            icon = Gtk.Image.new_from_icon_name("folder-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        
        name_box.pack_start(icon, False, False, 0)
        
        name_label = Gtk.Label(label=snapshot.name)
        name_label.set_halign(Gtk.Align.START)
        name_label.set_ellipsize(Pango.EllipsizeMode.END)
        name_box.pack_start(name_label, True, True, 0)
        
        # Add timestamp
        timestamp = datetime.datetime.fromisoformat(snapshot.timestamp)
        date_label = Gtk.Label(label=timestamp.strftime("%Y-%m-%d %H:%M"))
        date_label.set_halign(Gtk.Align.END)
        name_box.pack_end(date_label, False, False, 0)
        
        box.pack_start(name_box, False, False, 0)
        
        # Add description if available
        if snapshot.description:
            desc_label = Gtk.Label(label=snapshot.description)
            desc_label.set_halign(Gtk.Align.START)
            desc_label.set_ellipsize(Pango.EllipsizeMode.END)
            desc_label.get_style_context().add_class("snapshot-description")
            box.pack_start(desc_label, False, False, 0)
        
        row.add(box)
        return row
    
    def update_dashboard(self):
        """Update dashboard with current data."""
        try:
            # Get snapshots
            snapshots = self.snapshot_manager.get_snapshots()
            
            # Update total snapshots
            total = len(snapshots)
            self.update_stat_card(self.total_snapshots_card, str(total))
            
            # Count snapshot types
            btrfs_count = len([s for s in snapshots if s.type == "btrfs"])
            overlay_count = len([s for s in snapshots if s.type == "overlay"])
            
            # Update progress bars
            if total > 0:
                self.btrfs_progress.set_fraction(btrfs_count / total)
                self.btrfs_progress.set_text(f"BtrFS: {btrfs_count}")
                
                self.overlay_progress.set_fraction(overlay_count / total)
                self.overlay_progress.set_text(f"OverlayFS: {overlay_count}")
            else:
                self.btrfs_progress.set_fraction(0)
                self.btrfs_progress.set_text("BtrFS: 0")
                
                self.overlay_progress.set_fraction(0)
                self.overlay_progress.set_text("OverlayFS: 0")
            
            # Update storage usage
            from utils import get_disk_usage, format_size
            snapshot_dir = Path(self.snapshot_manager.config.get('snapshot_directory', '/var/lib/snapguard/snapshots'))
            if snapshot_dir.exists():
                usage = get_disk_usage(snapshot_dir)
                if usage:
                    self.update_stat_card(self.storage_card, format_size(usage['used']))
            
            # Update space saved (placeholder - would come from deduplication manager)
            # In a real implementation, this would be retrieved from the deduplication manager
            space_saved = 0
            for snapshot in snapshots:
                # This is just a placeholder calculation
                space_saved += snapshot.size * 0.3  # Assume 30% space saved
            
            self.update_stat_card(self.space_saved_card, format_size(int(space_saved)))
            
            # Update recent snapshots list
            # Clear existing rows
            for child in self.recent_list.get_children():
                self.recent_list.remove(child)
            
            # Add recent snapshots (up to 5)
            recent = sorted(snapshots, key=lambda s: s.timestamp, reverse=True)[:5]
            for snapshot in recent:
                row = self.create_snapshot_row(snapshot)
                self.recent_list.add(row)
            
            self.recent_list.show_all()
            
            # Update health indicators
            # Disk health
            if snapshot_dir.exists():
                usage = get_disk_usage(snapshot_dir)
                if usage and usage['percent'] < 80:
                    self.update_health_indicator(self.disk_health, "Good", "green")
                elif usage and usage['percent'] < 90:
                    self.update_health_indicator(self.disk_health, "Warning", "orange")
                else:
                    self.update_health_indicator(self.disk_health, "Critical", "red")
            
            # Snapshot integrity (placeholder)
            # In a real implementation, this would check actual snapshot integrity
            if total > 0:
                self.update_health_indicator(self.snapshot_health, "Good", "green")
            else:
                self.update_health_indicator(self.snapshot_health, "No Snapshots", "gray")
            
            # Backup status (placeholder)
            # In a real implementation, this would check actual backup status
            self.update_health_indicator(self.backup_health, "Good", "green")
            
        except Exception as e:
            print(f"Error updating dashboard: {e}")
    
    def update_stat_card(self, card, new_value):
        """Update the value in a stat card."""
        # Find the value label (second child of the content box)
        content_box = card.get_children()[1]
        value_label = content_box.get_children()[1]
        value_label.set_text(new_value)
    
    def update_health_indicator(self, indicator, status, color):
        """Update a health indicator with status and color."""
        status_label = indicator.get_children()[1]
        status_label.set_text(status)
        
        # Set color based on status
        if color == "green":
            status_label.set_markup(f"<span foreground='#2ec27e'>{status}</span>")
        elif color == "orange":
            status_label.set_markup(f"<span foreground='#e5a50a'>{status}</span>")
        elif color == "red":
            status_label.set_markup(f"<span foreground='#e01b24'>{status}</span>")
        else:
            status_label.set_markup(f"<span foreground='#9a9996'>{status}</span>")
    
    def on_refresh_clicked(self, button):
        """Handle refresh button click."""
        self.update_dashboard()
    
    def background_update(self):
        """Background thread to periodically update the dashboard."""
        while True:
            # Use GLib.idle_add to update UI from the main thread
            GLib.idle_add(self.update_dashboard)
            time.sleep(60)  # Update every minute