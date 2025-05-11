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

def initialize_panel(panel_instance, orientation=Gtk.Orientation.VERTICAL, spacing=6, 
                    snapshot_manager=None, parent_window=None):
    """
    Initialize common panel properties.
    
    Args:
        panel_instance: Panel instance to initialize
        orientation: Panel orientation
        spacing: Spacing between elements
        snapshot_manager: Snapshot manager instance
        parent_window: Parent window
    """
    super(panel_instance.__class__, panel_instance).__init__(orientation=orientation, spacing=spacing)
    panel_instance.logger = logging.getLogger(__name__)
    panel_instance.snapshot_manager = snapshot_manager
    panel_instance.parent_window = parent_window
    
    # Create UI elements
    panel_instance.create_widgets()
