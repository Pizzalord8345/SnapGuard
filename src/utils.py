#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os
import subprocess
from pathlib import Path  # This is a standard library import

# Blank line to separate standard library imports from third-party imports
import psutil  # Third-party import
import gi  # Third-party import
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

def setup_logging():
    """Sets up logging for the application."""
    log_dir = Path.home() / ".local" / "share" / "bettersync" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "bettersync.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def check_root_privileges():
    """Checks if the application is running with root privileges."""
    return os.geteuid() == 0 if hasattr(os, 'geteuid') else False

def run_command(cmd, check=True, capture_output=True):
    """Runs a command and returns the result."""
    try:
        result = subprocess.run(
            cmd, 
            check=check, 
            capture_output=capture_output, 
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        logging.error(f"Error executing command: {e}")
        return e

def is_btrfs_available():
    """Checks if Btrfs is available on the system."""
    try:
        result = run_command(["which", "btrfs"])
        return result.returncode == 0
    except Exception:
        return False

def is_overlayfs_available():
    """Checks if OverlayFS is available on the system."""
    try:
        with open('/proc/filesystems', 'r') as f:
            return 'overlay' in f.read()
    except Exception:
        return False

def get_disk_usage(path):
    """Returns the disk usage of a path."""
    try:
        usage = psutil.disk_usage(path)
        return {
            'total': usage.total,
            'used': usage.used,
            'free': usage.free,
            'percent': usage.percent
        }
    except Exception as e:
        logging.error(f"Error getting disk usage: {e}")
        return None

def show_error_dialog(parent, message, secondary_message=None):
    """Shows an error dialog."""
    dialog = Gtk.MessageDialog(
        parent=parent,
        flags=0,
        message_type=Gtk.MessageType.ERROR,
        buttons=Gtk.ButtonsType.OK,
        text=message
    )
    if secondary_message:
        dialog.format_secondary_text(secondary_message)
    dialog.run()
    dialog.destroy()

def show_confirmation_dialog(parent, message, secondary_message=None):
    """Shows a confirmation dialog and returns the response."""
    dialog = Gtk.MessageDialog(
        parent=parent,
        flags=0,
        message_type=Gtk.MessageType.QUESTION,
        buttons=Gtk.ButtonsType.YES_NO,
        text=message
    )
    if secondary_message:
        dialog.format_secondary_text(secondary_message)
    response = dialog.run()
    dialog.destroy()
    return response == Gtk.ResponseType.YES

def format_size(size_bytes):
    """Formats a size in bytes to a readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"
