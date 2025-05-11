import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, GLib

from snapguard import SnapGuard
from datetime import datetime

class SnapGuardGUI(Gtk.Window):
    def __init__(self):
        super().__init__(title="SnapGuard")
        self.snapguard = SnapGuard()
        self.set_default_size(800, 600)
        self.set_border_width(10)

        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(main_box)

        # Header area
        header_box = Gtk.Box(spacing=6)
        main_box.pack_start(header_box, False, False, 0)

        # Manual snapshot creation
        create_box = Gtk.Box(spacing=6)
        self.description_entry = Gtk.Entry()
        self.description_entry.set_placeholder_text("Description (optional)")
        create_button = Gtk.Button(label="Create Snapshot")
        create_button.connect("clicked", self.on_create_clicked)
        create_box.pack_start(self.description_entry, True, True, 0)
        create_box.pack_start(create_button, False, False, 0)
        header_box.pack_start(create_box, True, True, 0)

        # Schedule settings
        schedule_box = Gtk.Box(spacing=6)
        self.schedule_combo = Gtk.ComboBoxText()
        self.schedule_combo.append_text("Daily")
        self.schedule_combo.append_text("Weekly")
        self.schedule_combo.append_text("Monthly")
        self.schedule_combo.set_active(0)
        
        self.time_entry = Gtk.Entry()
        self.time_entry.set_text("02:00")
        self.time_entry.set_max_length(5)
        
        schedule_button = Gtk.Button(label="Update Schedule")
        schedule_button.connect("clicked", self.on_schedule_clicked)
        
        schedule_box.pack_start(self.schedule_combo, False, False, 0)
        schedule_box.pack_start(self.time_entry, False, False, 0)
        schedule_box.pack_start(schedule_button, False, False, 0)
        header_box.pack_start(schedule_box, False, False, 0)

        # Snapshot list
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        main_box.pack_start(scrolled_window, True, True, 0)

        # TreeView for snapshots
        self.liststore = Gtk.ListStore(str, str, str)
        self.treeview = Gtk.TreeView(model=self.liststore)
        
        # Columns
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Name", renderer, text=0)
        self.treeview.append_column(column)
        
        column = Gtk.TreeViewColumn("Created", renderer, text=1)
        self.treeview.append_column(column)
        
        column = Gtk.TreeViewColumn("Path", renderer, text=2)
        self.treeview.append_column(column)
        
        scrolled_window.add(self.treeview)

        # Action buttons
        button_box = Gtk.Box(spacing=6)
        main_box.pack_start(button_box, False, False, 0)

        delete_button = Gtk.Button(label="Delete Snapshot")
        delete_button.connect("clicked", self.on_delete_clicked)
        button_box.pack_start(delete_button, False, False, 0)

        restore_button = Gtk.Button(label="Restore Snapshot")
        restore_button.connect("clicked", self.on_restore_clicked)
        button_box.pack_start(restore_button, False, False, 0)

        # Status bar
        self.statusbar = Gtk.Statusbar()
        main_box.pack_start(self.statusbar, False, False, 0)

        # Initial update
        self.update_snapshot_list()

    def update_snapshot_list(self):
        """Updates the snapshot list in the GUI."""
        self.liststore.clear()
        snapshots = self.snapguard.list_snapshots()
        for snapshot in snapshots:
            self.liststore.append([
                snapshot['name'],
                snapshot['created'].strftime('%Y-%m-%d %H:%M:%S'),
                snapshot['path']
            ])

    def on_create_clicked(self, widget):
        """Handles the create snapshot button click."""
        description = self.description_entry.get_text()
        if self.snapguard.create_snapshot(description):
            self.statusbar.push(0, "Snapshot created successfully")
            self.update_snapshot_list()
        else:
            self.statusbar.push(0, "Error creating snapshot")

    def on_delete_clicked(self, widget):
        """Handles the delete snapshot button click."""
        selection = self.treeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter:
            snapshot_name = model[treeiter][0]
            if self.snapguard.delete_snapshot(snapshot_name):
                self.statusbar.push(0, "Snapshot deleted successfully")
                self.update_snapshot_list()
            else:
                self.statusbar.push(0, "Error deleting snapshot")

    def on_restore_clicked(self, widget):
        """Handles the restore snapshot button click."""
        selection = self.treeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter:
            snapshot_path = model[treeiter][2]
            # Here the restoration logic would be implemented
            self.statusbar.push(0, "Restoration started")

    def on_schedule_clicked(self, widget):
        """Handles the schedule update button click."""
        schedule_type = self.schedule_combo.get_active_text().lower()
        time = self.time_entry.get_text()
        if self.snapguard.update_schedule(schedule_type, time):
            self.statusbar.push(0, "Schedule updated successfully")
        else:
            self.statusbar.push(0, "Error updating schedule")

def main():
    win = SnapGuardGUI()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main() 