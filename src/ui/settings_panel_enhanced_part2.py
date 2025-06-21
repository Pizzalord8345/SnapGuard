#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
import logging
from pathlib import Path

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

# This file continues the EnhancedSettingsPanel class from settings_panel_enhanced.py

def create_performance_settings(self):
    """Create performance settings page."""
    page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    page.set_margin_top(12)
    page.set_margin_bottom(12)
    page.set_margin_start(12)
    page.set_margin_end(12)
    
    # Parallel processing settings
    parallel_frame = Gtk.Frame(label="Parallel Processing")
    parallel_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    parallel_box.set_margin_top(12)
    parallel_box.set_margin_bottom(12)
    parallel_box.set_margin_start(12)
    parallel_box.set_margin_end(12)
    
    # Enable parallel processing
    self.parallel_check = Gtk.CheckButton(label="Enable parallel processing")
    self.parallel_check.set_active(
        self.snapshot_manager.config.get('performance', {}).get('parallel_processing', {}).get('enabled', False)
    )
    parallel_box.pack_start(self.parallel_check, False, False, 0)
    
    # Worker count
    workers_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    workers_label = Gtk.Label(label="Maximum worker threads:")
    workers_label.set_halign(Gtk.Align.START)
    workers_box.pack_start(workers_label, False, False, 0)
    
    self.workers_spin = Gtk.SpinButton()
    self.workers_spin.set_range(1, 32)
    self.workers_spin.set_increments(1, 4)
    
    # Get worker count from config or default to CPU count - 1
    import multiprocessing
    default_workers = max(1, multiprocessing.cpu_count() - 1)
    self.workers_spin.set_value(
        self.snapshot_manager.config.get('performance', {}).get('parallel_processing', {}).get('max_workers', default_workers)
    )
    workers_box.pack_start(self.workers_spin, True, True, 0)
    
    parallel_box.pack_start(workers_box, False, False, 0)
    
    # Use processes instead of threads
    self.processes_check = Gtk.CheckButton(label="Use processes instead of threads (better for CPU-bound tasks)")
    self.processes_check.set_active(
        self.snapshot_manager.config.get('performance', {}).get('parallel_processing', {}).get('use_processes', False)
    )
    parallel_box.pack_start(self.processes_check, False, False, 0)
    
    parallel_frame.add(parallel_box)
    page.pack_start(parallel_frame, False, False, 0)
    
    # I/O throttling settings
    throttling_frame = Gtk.Frame(label="I/O Throttling")
    throttling_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    throttling_box.set_margin_top(12)
    throttling_box.set_margin_bottom(12)
    throttling_box.set_margin_start(12)
    throttling_box.set_margin_end(12)
    
    # Enable I/O throttling
    self.throttling_check = Gtk.CheckButton(label="Enable I/O throttling")
    self.throttling_check.set_active(
        self.snapshot_manager.config.get('storage', {}).get('io_throttling', {}).get('enabled', False)
    )
    throttling_box.pack_start(self.throttling_check, False, False, 0)
    
    # Read speed limit
    read_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    read_label = Gtk.Label(label="Maximum read speed (MB/s):")
    read_label.set_halign(Gtk.Align.START)
    read_box.pack_start(read_label, False, False, 0)
    
    self.read_spin = Gtk.SpinButton()
    self.read_spin.set_range(0, 1000)
    self.read_spin.set_increments(10, 50)
    self.read_spin.set_value(
        self.snapshot_manager.config.get('storage', {}).get('io_throttling', {}).get('max_read_mbps', 100)
    )
    read_box.pack_start(self.read_spin, True, True, 0)
    
    throttling_box.pack_start(read_box, False, False, 0)
    
    # Write speed limit
    write_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    write_label = Gtk.Label(label="Maximum write speed (MB/s):")
    write_label.set_halign(Gtk.Align.START)
    write_box.pack_start(write_label, False, False, 0)
    
    self.write_spin = Gtk.SpinButton()
    self.write_spin.set_range(0, 1000)
    self.write_spin.set_increments(10, 50)
    self.write_spin.set_value(
        self.snapshot_manager.config.get('storage', {}).get('io_throttling', {}).get('max_write_mbps', 50)
    )
    write_box.pack_start(self.write_spin, True, True, 0)
    
    throttling_box.pack_start(write_box, False, False, 0)
    
    throttling_frame.add(throttling_box)
    page.pack_start(throttling_frame, False, False, 0)
    
    # Smart scheduling settings
    scheduling_frame = Gtk.Frame(label="Smart Scheduling")
    scheduling_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    scheduling_box.set_margin_top(12)
    scheduling_box.set_margin_bottom(12)
    scheduling_box.set_margin_start(12)
    scheduling_box.set_margin_end(12)
    
    # Enable smart scheduling
    self.scheduling_check = Gtk.CheckButton(label="Enable smart scheduling (run operations during system idle time)")
    self.scheduling_check.set_active(
        self.snapshot_manager.config.get('performance', {}).get('smart_scheduling', {}).get('enabled', False)
    )
    scheduling_box.pack_start(self.scheduling_check, False, False, 0)
    
    # CPU threshold
    cpu_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    cpu_label = Gtk.Label(label="CPU usage threshold (%):")
    cpu_label.set_halign(Gtk.Align.START)
    cpu_box.pack_start(cpu_label, False, False, 0)
    
    self.cpu_spin = Gtk.SpinButton()
    self.cpu_spin.set_range(10, 90)
    self.cpu_spin.set_increments(5, 10)
    self.cpu_spin.set_value(
        self.snapshot_manager.config.get('performance', {}).get('smart_scheduling', {}).get('cpu_threshold', 30)
    )
    cpu_box.pack_start(self.cpu_spin, True, True, 0)
    
    scheduling_box.pack_start(cpu_box, False, False, 0)
    
    # Quiet hours
    hours_label = Gtk.Label(label="Quiet hours (when system is considered idle):")
    hours_label.set_halign(Gtk.Align.START)
    scheduling_box.pack_start(hours_label, False, False, 0)
    
    hours_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    
    start_label = Gtk.Label(label="Start:")
    start_label.set_halign(Gtk.Align.START)
    hours_box.pack_start(start_label, False, False, 0)
    
    self.start_entry = Gtk.Entry()
    self.start_entry.set_text(
        self.snapshot_manager.config.get('performance', {}).get('smart_scheduling', {}).get('quiet_hours_start', "22:00")
    )
    self.start_entry.set_placeholder_text("HH:MM")
    hours_box.pack_start(self.start_entry, True, True, 0)
    
    end_label = Gtk.Label(label="End:")
    end_label.set_halign(Gtk.Align.START)
    hours_box.pack_start(end_label, False, False, 0)
    
    self.end_entry = Gtk.Entry()
    self.end_entry.set_text(
        self.snapshot_manager.config.get('performance', {}).get('smart_scheduling', {}).get('quiet_hours_end', "06:00")
    )
    self.end_entry.set_placeholder_text("HH:MM")
    hours_box.pack_start(self.end_entry, True, True, 0)
    
    scheduling_box.pack_start(hours_box, False, False, 0)
    
    scheduling_frame.add(scheduling_box)
    page.pack_start(scheduling_frame, False, False, 0)
    
    return page

def create_storage_settings(self):
    """Create storage settings page."""
    page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    page.set_margin_top(12)
    page.set_margin_bottom(12)
    page.set_margin_start(12)
    page.set_margin_end(12)
    
    # Deduplication settings
    dedup_frame = Gtk.Frame(label="Deduplication")
    dedup_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    dedup_box.set_margin_top(12)
    dedup_box.set_margin_bottom(12)
    dedup_box.set_margin_start(12)
    dedup_box.set_margin_end(12)
    
    # Enable deduplication
    self.dedup_check = Gtk.CheckButton(label="Enable deduplication")
    self.dedup_check.set_active(
        self.snapshot_manager.config.get('storage', {}).get('deduplication', {}).get('enabled', False)
    )
    dedup_box.pack_start(self.dedup_check, False, False, 0)
    
    # Deduplication method
    method_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    method_label = Gtk.Label(label="Deduplication method:")
    method_label.set_halign(Gtk.Align.START)
    method_box.pack_start(method_label, False, False, 0)
    
    self.method_combo = Gtk.ComboBoxText()
    self.method_combo.append_text("file")
    self.method_combo.append_text("block")
    
    # Set active method
    if self.snapshot_manager.config.get('storage', {}).get('deduplication', {}).get('method', "file") == "file":
        self.method_combo.set_active(0)
    else:
        self.method_combo.set_active(1)
    
    method_box.pack_start(self.method_combo, True, True, 0)
    
    dedup_box.pack_start(method_box, False, False, 0)
    
    # Block size (only relevant for block-level deduplication)
    block_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    block_label = Gtk.Label(label="Block size (bytes):")
    block_label.set_halign(Gtk.Align.START)
    block_box.pack_start(block_label, False, False, 0)
    
    self.block_spin = Gtk.SpinButton()
    self.block_spin.set_range(1024, 1048576)  # 1KB to 1MB
    self.block_spin.set_increments(1024, 4096)
    self.block_spin.set_value(
        self.snapshot_manager.config.get('storage', {}).get('deduplication', {}).get('block_size', 4096)
    )
    block_box.pack_start(self.block_spin, True, True, 0)
    
    dedup_box.pack_start(block_box, False, False, 0)
    
    # Run deduplication now button
    dedup_button = Gtk.Button(label="Run Deduplication Now")
    dedup_button.connect("clicked", self.on_run_dedup_clicked)
    dedup_box.pack_start(dedup_button, False, False, 0)
    
    dedup_frame.add(dedup_box)
    page.pack_start(dedup_frame, False, False, 0)
    
    # Compression settings
    compression_frame = Gtk.Frame(label="Compression")
    compression_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    compression_box.set_margin_top(12)
    compression_box.set_margin_bottom(12)
    compression_box.set_margin_start(12)
    compression_box.set_margin_end(12)
    
    # Enable compression
    self.compression_check = Gtk.CheckButton(label="Enable compression")
    self.compression_check.set_active(
        self.snapshot_manager.config.get('storage', {}).get('compression', {}).get('enabled', False)
    )
    compression_box.pack_start(self.compression_check, False, False, 0)
    
    # Compression algorithm
    algo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    algo_label = Gtk.Label(label="Compression algorithm:")
    algo_label.set_halign(Gtk.Align.START)
    algo_box.pack_start(algo_label, False, False, 0)
    
    self.comp_algo_combo = Gtk.ComboBoxText()
    self.comp_algo_combo.append_text("zstd")
    self.comp_algo_combo.append_text("lz4")
    self.comp_algo_combo.append_text("gzip")
    
    # Set active algorithm
    algo = self.snapshot_manager.config.get('storage', {}).get('compression', {}).get('algorithm', "zstd")
    if algo == "zstd":
        self.comp_algo_combo.set_active(0)
    elif algo == "lz4":
        self.comp_algo_combo.set_active(1)
    else:
        self.comp_algo_combo.set_active(2)
    
    algo_box.pack_start(self.comp_algo_combo, True, True, 0)
    
    compression_box.pack_start(algo_box, False, False, 0)
    
    # Compression level
    level_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    level_label = Gtk.Label(label="Compression level:")
    level_label.set_halign(Gtk.Align.START)
    level_box.pack_start(level_label, False, False, 0)
    
    self.level_spin = Gtk.SpinButton()
    self.level_spin.set_range(1, 9)
    self.level_spin.set_increments(1, 2)
    self.level_spin.set_value(
        self.snapshot_manager.config.get('storage', {}).get('compression', {}).get('level', 3)
    )
    level_box.pack_start(self.level_spin, True, True, 0)
    
    compression_box.pack_start(level_box, False, False, 0)
    
    compression_frame.add(compression_box)
    page.pack_start(compression_frame, False, False, 0)
    
    return page