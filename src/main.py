#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
import os
import sys
import logging
from pathlib import Path

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

# Import own modules
from snapshot_manager import SnapshotManager
from ui.main_window import MainWindow
from utils import check_root_privileges, setup_logging

def main():
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Check root privileges
    if not check_root_privileges():
        logger.warning("Application started without root privileges. Some features may be limited.")
        # A dialog could be shown here
    
    # Initialize Snapshot Manager
    snapshot_manager = SnapshotManager()
    
    # Create and start main window
    window = MainWindow(snapshot_manager)
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    
    # Start GTK main loop
    Gtk.main()

if __name__ == "__main__":
    main()
