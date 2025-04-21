#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI utility functions for BetterSync application.

This module provides common UI helper functions to reduce code duplication.
"""

import logging
from gi.repository import Gtk

def create_folder_chooser_dialog(parent, title):
    """
    Creates a folder chooser dialog with standard buttons.
    
    Args:
        parent: Parent window for the dialog
        title: Title of the dialog
        
    Returns:
        The created dialog
    """
    dialog = Gtk.FileChooserDialog(
        title=title,
        parent=parent,
        action=Gtk.FileChooserAction.SELECT_FOLDER
    )
    dialog.add_buttons(
        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
        Gtk.STOCK_OPEN, Gtk.ResponseType.OK
    )
    return dialog

def initialize_panel(self, orientation=Gtk.Orientation.VERTICAL, spacing=6, 
                    snapshot_manager=None, parent_window=None):
    """
    Initialize common panel properties.
    
    Args:
        self: Panel instance
        orientation: Panel orientation
        spacing: Spacing between elements
        snapshot_manager: Snapshot manager instance
        parent_window: Parent window
    """
    super(self.__class__, self).__init__(orientation=orientation, spacing=spacing)
    self.logger = logging.getLogger(__name__)
    self.snapshot_manager = snapshot_manager
    self.parent_window = parent_window
    
    # Create UI elements
    self.create_widgets()
