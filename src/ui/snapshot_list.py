#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
import logging
import datetime
from pathlib import Path

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Pango, Gdk

from utils import show_error_dialog, show_confirmation_dialog, format_size

class SnapshotList(Gtk.Box):
    """Panel for displaying and managing snapshots."""
    
    def __init__(self, snapshot_manager, parent_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.logger = logging.getLogger(__name__)
        self.snapshot_manager = snapshot_manager
        self.parent_window = parent_window
        
        # UI-Elemente erstellen
        self.create_widgets()
        
        # Snapshots laden
        self.refresh()
    
    def create_widgets(self):
        """Erstellt die UI-Elemente."""
        # Toolbar
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.pack_start(toolbar, False, False, 0)
        
        # Filter-Dropdown
        filter_label = Gtk.Label(label="Filter:")
        toolbar.pack_start(filter_label, False, False, 0)
        
        self.filter_combo = Gtk.ComboBoxText()
        self.filter_combo.append_text("All Snapshots")
        self.filter_combo.append_text("Btrfs Snapshots")
        self.filter_combo.append_text("OverlayFS Snapshots")
        self.filter_combo.set_active(0)
        self.filter_combo.connect("changed", self.on_filter_changed)
        toolbar.pack_start(self.filter_combo, False, False, 0)
        
        # Neuer Snapshot-Button
        new_button = Gtk.Button(label="Create New")
        new_button.connect("clicked", self.on_new_snapshot_clicked)
        toolbar.pack_end(new_button, False, False, 0)
        
        # Trenner
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.pack_start(separator, False, False, 0)
        
        # Snapshot-Liste (TreeView)
        self.create_snapshot_treeview()
        
        # Details-Bereich
        self.create_details_area()
    
    def create_snapshot_treeview(self):
        """Erstellt die TreeView für die Snapshot-Liste."""
        # Scrolled Window
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        self.pack_start(scrolled_window, True, True, 0)
        
        # TreeView und Model
        self.snapshot_store = Gtk.ListStore(str, str, str, str, str, str, int, bool, bool)  # ID, Name, Typ, Pfad, Zeitstempel, Beschreibung, Größe, Aktiv, Auto
        self.snapshot_view = Gtk.TreeView(model=self.snapshot_store)
        
        # Spalten
        self.add_column("Name", 1)
        self.add_column("Type", 2)
        self.add_column("Created", 4)
        self.add_column("Size", 6, cell_renderer=self.size_cell_data_func)
        self.add_column("Active", 7, cell_renderer=self.boolean_cell_data_func)
        self.add_column("Auto", 8, cell_renderer=self.boolean_cell_data_func)
        
        # Sortierung aktivieren
        self.snapshot_store.set_sort_column_id(4, Gtk.SortType.DESCENDING)
        
        # Auswahl
        self.selection = self.snapshot_view.get_selection()
        self.selection.connect("changed", self.on_snapshot_selection_changed)
        
        scrolled_window.add(self.snapshot_view)
    
    def add_column(self, title, column_id, cell_renderer=None):
        """Fügt eine Spalte zur TreeView hinzu."""
        if cell_renderer:
            if title == "Size":
                renderer = Gtk.CellRendererText()
                column = Gtk.TreeViewColumn(title, renderer)
                column.set_cell_data_func(renderer, cell_renderer)
            elif title in ["Active", "Auto"]:
                renderer = Gtk.CellRendererToggle()
                renderer.set_activatable(False)
                column = Gtk.TreeViewColumn(title, renderer)
                column.set_cell_data_func(renderer, cell_renderer)
            else:
                renderer = Gtk.CellRendererText()
                column = Gtk.TreeViewColumn(title, renderer, text=column_id)
        else:
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=column_id)
        
        column.set_resizable(True)
        column.set_sort_column_id(column_id)
        self.snapshot_view.append_column(column)
    
    def size_cell_data_func(self, column, cell, model, iter, data):
        """Formatiert die Größe im menschenlesbaren Format."""
        size = model.get_value(iter, 6)
        cell.set_property("text", format_size(size))
    
    def boolean_cell_data_func(self, column, cell, model, iter, data):
        """Formatiert boolesche Werte für die Anzeige."""
        if column.get_title() == "Active":
            value = model.get_value(iter, 7)
        else:  # Auto
            value = model.get_value(iter, 8)
        cell.set_property("active", value)
    
    def create_details_area(self):
        """Erstellt den Bereich für die Snapshot-Details."""
        # Details-Grid
        details_frame = Gtk.Frame(label="Snapshot Details")
        self.pack_start(details_frame, False, False, 0)
        
        details_grid = Gtk.Grid()
        details_grid.set_column_spacing(12)
        details_grid.set_row_spacing(6)
        details_grid.set_margin_top(12)
        details_grid.set_margin_bottom(12)
        details_grid.set_margin_start(12)
        details_grid.set_margin_end(12)
        details_frame.add(details_grid)
        
        # Labels für Details
        labels = ["ID:", "Name:", "Type:", "Path:", "Created:", "Description:", "Size:", "Status:"]
        self.detail_values = {}
        
        for i, label_text in enumerate(labels):
            label = Gtk.Label(label=label_text)
            label.set_halign(Gtk.Align.START)
            details_grid.attach(label, 0, i, 1, 1)
            
            value_label = Gtk.Label(label="-")
            value_label.set_halign(Gtk.Align.START)
            value_label.set_hexpand(True)
            value_label.set_ellipsize(Pango.EllipsizeMode.END)
            details_grid.attach(value_label, 1, i, 1, 1)
            
            self.detail_values[label_text[:-1].lower()] = value_label
        
        # Aktions-Buttons
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        action_box.set_margin_top(12)
        details_grid.attach(action_box, 0, len(labels), 2, 1)
        
        self.restore_button = Gtk.Button(label="Restore")
        self.restore_button.connect("clicked", self.on_restore_clicked)
        self.restore_button.set_sensitive(False)
        action_box.pack_start(self.restore_button, True, True, 0)
        
        self.delete_button = Gtk.Button(label="Delete")
        self.delete_button.connect("clicked", self.on_delete_clicked)
        self.delete_button.set_sensitive(False)
        action_box.pack_start(self.delete_button, True, True, 0)
        
        self.live_button = Gtk.Button(label="Activate Live Mode")
        self.live_button.connect("clicked", self.on_live_mode_clicked)
        self.live_button.set_sensitive(False)
        action_box.pack_start(self.live_button, True, True, 0)
    
    def refresh(self):
        """Aktualisiert die Snapshot-Liste."""
        # Daten laden
        self.snapshot_store.clear()
        
        # Filter anwenden
        filter_option = self.filter_combo.get_active()
        snapshots = []
        
        if filter_option == 0:  # Alle
            snapshots = self.snapshot_manager.get_snapshots()
        elif filter_option == 1:  # Btrfs
            snapshots = self.snapshot_manager.get_snapshots("btrfs")
        elif filter_option == 2:  # OverlayFS
            snapshots = self.snapshot_manager.get_snapshots("overlay")
        
        # Liste füllen
        for snapshot in snapshots:
            self.snapshot_store.append([
                snapshot.id,
                snapshot.name,
                "Btrfs" if snapshot.type == "btrfs" else "OverlayFS",
                snapshot.path,
                snapshot.timestamp,
                snapshot.description,
                snapshot.size,
                snapshot.is_active,
                snapshot.is_auto
            ])
        
        # Details zurücksetzen
        self.clear_details()
    
    def clear_details(self):
        """Leert den Details-Bereich."""
        for value_label in self.detail_values.values():
            value_label.set_text("-")
        
        self.restore_button.set_sensitive(False)
        self.delete_button.set_sensitive(False)
        self.live_button.set_sensitive(False)
    
    def on_filter_changed(self, combo):
        """Handler für Änderungen am Filter."""
        self.refresh()
    
    def on_snapshot_selection_changed(self, selection):
        """Handler für die Auswahl eines Snapshots."""
        model, treeiter = selection.get_selected()
        if treeiter is not None:
            # Daten extrahieren
            snapshot_id = model[treeiter][0]
            name = model[treeiter][1]
            snapshot_type = model[treeiter][2]
            path = model[treeiter][3]
            timestamp = model[treeiter][4]
            description = model[treeiter][5]
            size = model[treeiter][6]
            is_active = model[treeiter][7]
            is_auto = model[treeiter][8]
            
            # Details aktualisieren
            self.detail_values["id"].set_text(snapshot_id)
            self.detail_values["name"].set_text(name)
            self.detail_values["type"].set_text(snapshot_type)
            self.detail_values["path"].set_text(path)
            self.detail_values["created"].set_text(timestamp)
            self.detail_values["description"].set_text(description or "-")
            self.detail_values["size"].set_text(format_size(size))
            
            status_text = "Active" if is_active else "Inactive"
            if is_auto:
                status_text += ", Auto"
            self.detail_values["status"].set_text(status_text)
            
            # Buttons aktivieren
            self.restore_button.set_sensitive(True)
            self.delete_button.set_sensitive(not is_active)
            self.live_button.set_sensitive(snapshot_type == "OverlayFS" and not is_active)
        else:
            self.clear_details()
    
    def on_new_snapshot_clicked(self, button):
        """Handler für den 'Neuer Snapshot'-Button."""
        dialog = NewSnapshotDialog(self.parent_window, self.snapshot_manager)
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            # Snapshot erstellen basierend auf den Dialog-Eingaben
            snapshot_type = dialog.get_snapshot_type()
            name = dialog.get_name()
            source_path = dialog.get_source_path()
            description = dialog.get_description()
            
            # Snapshot erstellen
            if snapshot_type == "btrfs":
                snapshot = self.snapshot_manager.create_btrfs_snapshot(name, source_path, description)
            else:  # overlay
                snapshot = self.snapshot_manager.create_overlay_snapshot(name, source_path, description)
            
            if snapshot:
                self.refresh()
                self.parent_window.update_status()
                self.parent_window.show_message(f"Snapshot '{name}' created")
            else:
                show_error_dialog(
                    self.parent_window,
                    f"Error creating snapshot",
                    f"The {snapshot_type} snapshot could not be created. See log file for details."
                )
        
        dialog.destroy()
    
    def on_restore_clicked(self, button):
        """Handler für den 'Wiederherstellen'-Button."""
        model, treeiter = self.selection.get_selected()
        if treeiter is None:
            return
        
        snapshot_id = model[treeiter][0]
        name = model[treeiter][1]
        
        # Dialog zur Auswahl des Zielpfads
        dialog = Gtk.FileChooserDialog(
            title="Select target path",
            parent=self.parent_window,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            "Restore", Gtk.ResponseType.OK
        )
        
        # Dialog konfigurieren
        dialog.set_default_size(800, 600)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            target_path = dialog.get_filename()
            dialog.destroy()
            
            # Bestätigung
            confirm = show_confirmation_dialog(
                self.parent_window,
                f"Restore snapshot '{name}'?",
                f"The snapshot will be restored to {target_path}. Existing files may be overwritten."
            )
            
            if confirm:
                # Snapshot wiederherstellen
                success = self.snapshot_manager.restore_snapshot(snapshot_id, target_path)
                
                if success:
                    self.parent_window.show_message(f"Snapshot '{name}' restored to {target_path}")
                else:
                    show_error_dialog(
                        self.parent_window,
                        "Error restoring snapshot",
                        f"The snapshot could not be restored. See log file for details."
                    )
        else:
            dialog.destroy()
    
    def on_delete_clicked(self, button):
        """Handler für den 'Löschen'-Button."""
        model, treeiter = self.selection.get_selected()
        if treeiter is None:
            return
        
        snapshot_id = model[treeiter][0]
        name = model[treeiter][1]
        
        # Bestätigung
        confirm = show_confirmation_dialog(
            self.parent_window,
            f"Delete snapshot '{name}'?",
            "This action cannot be undone."
        )
        
        if confirm:
            # Snapshot löschen
            success = self.snapshot_manager.delete_snapshot(snapshot_id)
            
            if success:
                self.refresh()
                self.parent_window.update_status()
                self.parent_window.show_message(f"Snapshot '{name}' deleted")
            else:
                show_error_dialog(
                    self.parent_window,
                    "Error deleting snapshot",
                    f"The snapshot could not be deleted. See log file for details."
                )
    
    def on_live_mode_clicked(self, button):
        """Handler für den 'In Live-Modus aktivieren'-Button."""
        model, treeiter = self.selection.get_selected()
        if treeiter is None:
            return
        
        snapshot_id = model[treeiter][0]
        name = model[treeiter][1]
        
        # Zum Live-Modus-Tab wechseln
        self.parent_window.stack.set_visible_child_name("live_mode")
        
        # Snapshot auswählen
        self.parent_window.live_mode_panel.select_snapshot(snapshot_id)


class NewSnapshotDialog(Gtk.Dialog):
    """Dialog zum Erstellen eines neuen Snapshots."""
    
    def __init__(self, parent, snapshot_manager):
        super().__init__(
            title="Create New Snapshot",
            parent=parent,
            flags=0
        )
        self.snapshot_manager = snapshot_manager
        
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        
        self.set_default_size(500, 400)
        
        # Content area
        content_area = self.get_content_area()
        content_area.set_margin_top(12)
        content_area.set_margin_bottom(12)
        content_area.set_margin_start(12)
        content_area.set_margin_end(12)
        content_area.set_spacing(6)
        
        # Formular für Snapshot-Erstellung
        grid = Gtk.Grid()
        grid.set_column_spacing(12)
        grid.set_row_spacing(12)
        content_area.add(grid)
        
        # Snapshot-Typ
        type_label = Gtk.Label(label="Snapshot Type:")
        type_label.set_halign(Gtk.Align.START)
        grid.attach(type_label, 0, 0, 1, 1)
        
        self.type_combo = Gtk.ComboBoxText()
        
        if self.snapshot_manager.btrfs_available:
            self.type_combo.append_text("Btrfs (persistent)")
        
        if self.snapshot_manager.overlayfs_available:
            self.type_combo.append_text("OverlayFS (temporary)")
        
        self.type_combo.set_active(0)
        grid.attach(self.type_combo, 1, 0, 1, 1)
        
        # Name
        name_label = Gtk.Label(label="Name:")
        name_label.set_halign(Gtk.Align.START)
        grid.attach(name_label, 0, 1, 1, 1)
        
        self.name_entry = Gtk.Entry()
        self.name_entry.set_hexpand(True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.name_entry.set_text(f"Snapshot_{timestamp}")
        grid.attach(self.name_entry, 1, 1, 1, 1)
        
        # Quellpfad
        source_label = Gtk.Label(label="Source Path:")
        source_label.set_halign(Gtk.Align.START)
        grid.attach(source_label, 0, 2, 1, 1)
        
        source_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        grid.attach(source_box, 1, 2, 1, 1)
        
        self.source_entry = Gtk.Entry()
        self.source_entry.set_hexpand(True)
        source_box.pack_start(self.source_entry, True, True, 0)
        
        browse_button = Gtk.Button(label="Browse...")
        browse_button.connect("clicked", self.on_browse_clicked)
        source_box.pack_start(browse_button, False, False, 0)
        
        # Beschreibung
        desc_label = Gtk.Label(label="Description:")
        desc_label.set_halign(Gtk.Align.START)
        grid.attach(desc_label, 0, 3, 1, 1)
        
        self.desc_text = Gtk.TextView()
        self.desc_text.set_wrap_mode(Gtk.WrapMode.WORD)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(self.desc_text)
        grid.attach(scrolled, 1, 3, 1, 1)
        
        self.show_all()
    
    def on_browse_clicked(self, button):
        """Handler für den 'Durchsuchen'-Button."""
        dialog = Gtk.FileChooserDialog(
            title="Select source path",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.source_entry.set_text(dialog.get_filename())
        
        dialog.destroy()
    
    def get_snapshot_type(self):
        """Gibt den ausgewählten Snapshot-Typ zurück."""
        type_text = self.type_combo.get_active_text()
        if type_text and "Btrfs" in type_text:
            return "btrfs"
        return "overlay"
    
    def get_name(self):
        """Gibt den eingegebenen Namen zurück."""
        return self.name_entry.get_text()
    
    def get_source_path(self):
        """Gibt den eingegebenen Quellpfad zurück."""
        return self.source_entry.get_text()
    
    def get_description(self):
        """Gibt die eingegebene Beschreibung zurück."""
        buffer = self.desc_text.get_buffer()
        start, end = buffer.get_bounds()
        return buffer.get_text(start, end, False)
