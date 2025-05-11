#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

class ThemeManager:
    """
    Manages application themes including dark mode support.
    """
    
    THEME_LIGHT = "light"
    THEME_DARK = "dark"
    THEME_SYSTEM = "system"
    
    def __init__(self):
        self.settings = Gtk.Settings.get_default()
        self._current_theme = self.THEME_LIGHT
    
    def set_theme(self, theme_name: str) -> bool:
        """
        Set the application theme.
        
        Args:
            theme_name: Name of the theme (light, dark, system)
            
        Returns:
            True if theme was set successfully, False otherwise
        """
        if theme_name == self.THEME_LIGHT:
            self.settings.set_property("gtk-application-prefer-dark-theme", False)
            self._current_theme = self.THEME_LIGHT
            return True
        
        elif theme_name == self.THEME_DARK:
            self.settings.set_property("gtk-application-prefer-dark-theme", True)
            self._current_theme = self.THEME_DARK
            return True
        
        elif theme_name == self.THEME_SYSTEM:
            # Try to detect system theme
            try:
                # This is a simplified approach - in a real application,
                # you would use platform-specific methods to detect the system theme
                
                # For GNOME, you could use:
                # gsettings get org.gnome.desktop.interface gtk-theme
                
                # For now, we'll just use a placeholder implementation
                import subprocess
                try:
                    result = subprocess.run(
                        ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        theme = result.stdout.strip().strip("'")
                        is_dark = "dark" in theme.lower()
                        self.settings.set_property("gtk-application-prefer-dark-theme", is_dark)
                        self._current_theme = self.THEME_DARK if is_dark else self.THEME_LIGHT
                        return True
                except Exception:
                    pass
                
                # Fallback to light theme
                self.settings.set_property("gtk-application-prefer-dark-theme", False)
                self._current_theme = self.THEME_LIGHT
                return True
            
            except Exception:
                # Fallback to light theme
                self.settings.set_property("gtk-application-prefer-dark-theme", False)
                self._current_theme = self.THEME_LIGHT
                return False
        
        return False
    
    def get_current_theme(self) -> str:
        """
        Get the current theme name.
        
        Returns:
            Name of the current theme
        """
        return self._current_theme
    
    def is_dark_theme(self) -> bool:
        """
        Check if dark theme is currently active.
        
        Returns:
            True if dark theme is active, False otherwise
        """
        return self._current_theme == self.THEME_DARK
    
    def toggle_theme(self) -> str:
        """
        Toggle between light and dark themes.
        
        Returns:
            Name of the new theme
        """
        if self._current_theme == self.THEME_DARK:
            self.set_theme(self.THEME_LIGHT)
        else:
            self.set_theme(self.THEME_DARK)
        
        return self._current_theme


class DarkThemeProvider:
    """
    Provides CSS for dark theme styling.
    """
    
    @staticmethod
    def get_dark_css() -> str:
        """
        Get CSS for dark theme.
        
        Returns:
            CSS string
        """
        return """
        /* Dark theme CSS */
        
        /* Main window */
        window {
            background-color: #2d2d2d;
            color: #e0e0e0;
        }
        
        /* Header bar */
        headerbar {
            background-color: #1e1e1e;
            border-bottom: 1px solid #3c3c3c;
        }
        
        /* Buttons */
        button {
            background-color: #3c3c3c;
            color: #e0e0e0;
            border: 1px solid #505050;
        }
        
        button:hover {
            background-color: #505050;
        }
        
        button:active {
            background-color: #606060;
        }
        
        /* Text entries */
        entry {
            background-color: #3c3c3c;
            color: #e0e0e0;
            border: 1px solid #505050;
        }
        
        /* Lists and trees */
        treeview {
            background-color: #2d2d2d;
            color: #e0e0e0;
        }
        
        treeview:selected {
            background-color: #3584e4;
            color: #ffffff;
        }
        
        /* Scrollbars */
        scrollbar {
            background-color: #2d2d2d;
        }
        
        scrollbar slider {
            background-color: #505050;
            border-radius: 6px;
        }
        
        scrollbar slider:hover {
            background-color: #606060;
        }
        
        /* Notebooks */
        notebook > header {
            background-color: #2d2d2d;
        }
        
        notebook > header > tabs > tab {
            background-color: #3c3c3c;
            color: #e0e0e0;
        }
        
        notebook > header > tabs > tab:checked {
            background-color: #505050;
        }
        
        /* Progress bars */
        progressbar trough {
            background-color: #3c3c3c;
        }
        
        progressbar progress {
            background-color: #3584e4;
        }
        
        /* Switches */
        switch {
            background-color: #3c3c3c;
        }
        
        switch:checked {
            background-color: #3584e4;
        }
        
        /* Checkboxes */
        checkbutton check {
            background-color: #3c3c3c;
            border: 1px solid #505050;
        }
        
        checkbutton:checked check {
            background-color: #3584e4;
        }
        
        /* Radio buttons */
        radiobutton radio {
            background-color: #3c3c3c;
            border: 1px solid #505050;
        }
        
        radiobutton:checked radio {
            background-color: #3584e4;
        }
        
        /* Separators */
        separator {
            background-color: #505050;
        }
        
        /* Tooltips */
        tooltip {
            background-color: #1e1e1e;
            color: #e0e0e0;
        }
        
        /* Menus */
        menu {
            background-color: #2d2d2d;
            color: #e0e0e0;
        }
        
        menuitem {
            color: #e0e0e0;
        }
        
        menuitem:hover {
            background-color: #3584e4;
        }
        
        /* Popovers */
        popover {
            background-color: #2d2d2d;
            color: #e0e0e0;
        }
        
        /* Custom classes for SnapGuard */
        .snapshot-item {
            background-color: #3c3c3c;
            border-radius: 6px;
            padding: 8px;
            margin: 4px;
        }
        
        .snapshot-item:selected {
            background-color: #3584e4;
        }
        
        .snapshot-name {
            font-weight: bold;
            color: #e0e0e0;
        }
        
        .snapshot-date {
            color: #b0b0b0;
            font-size: 0.9em;
        }
        
        .snapshot-description {
            color: #c0c0c0;
            font-style: italic;
        }
        
        .dashboard-card {
            background-color: #3c3c3c;
            border-radius: 8px;
            padding: 12px;
            margin: 8px;
        }
        
        .dashboard-title {
            font-weight: bold;
            font-size: 1.2em;
            color: #e0e0e0;
        }
        
        .dashboard-value {
            font-size: 2em;
            color: #3584e4;
        }
        
        .dashboard-subtitle {
            color: #b0b0b0;
            font-size: 0.9em;
        }
        
        .critical-action {
            background-color: #c01c28;
            color: #ffffff;
        }
        
        .critical-action:hover {
            background-color: #e01b24;
        }
        
        .success-action {
            background-color: #26a269;
            color: #ffffff;
        }
        
        .success-action:hover {
            background-color: #2ec27e;
        }
        """
    
    @staticmethod
    def apply_css_to_widget(widget: Gtk.Widget) -> None:
        """
        Apply dark theme CSS to a widget.
        
        Args:
            widget: Widget to apply CSS to
        """
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(DarkThemeProvider.get_dark_css().encode())
        
        context = widget.get_style_context()
        screen = Gdk.Screen.get_default()
        
        context.add_provider_for_screen(
            screen,
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


def create_theme_switcher() -> Gtk.Box:
    """
    Create a theme switcher widget.
    
    Returns:
        Box containing the theme switcher
    """
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    
    # Create theme manager
    theme_manager = ThemeManager()
    
    # Create theme label
    label = Gtk.Label(label="Theme:")
    box.pack_start(label, False, False, 6)
    
    # Create theme combo box
    combo = Gtk.ComboBoxText()
    combo.append_text("Light")
    combo.append_text("Dark")
    combo.append_text("System")
    
    # Set initial value
    current_theme = theme_manager.get_current_theme()
    if current_theme == ThemeManager.THEME_LIGHT:
        combo.set_active(0)
    elif current_theme == ThemeManager.THEME_DARK:
        combo.set_active(1)
    else:
        combo.set_active(2)
    
    # Connect signal
    def on_theme_changed(combo):
        index = combo.get_active()
        if index == 0:
            theme_manager.set_theme(ThemeManager.THEME_LIGHT)
        elif index == 1:
            theme_manager.set_theme(ThemeManager.THEME_DARK)
        else:
            theme_manager.set_theme(ThemeManager.THEME_SYSTEM)
    
    combo.connect("changed", on_theme_changed)
    box.pack_start(combo, False, False, 0)
    
    return box