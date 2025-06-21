#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import threading
import queue
import time
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import List, Dict, Callable, Any, Optional, Tuple, Union
from pathlib import Path

class ParallelProcessor:
    """
    Handles parallel processing operations for improved performance.
    Supports both multi-threading and multi-processing.
    """
    
    def __init__(self, max_workers: Optional[int] = None, use_processes: bool = False):
        """
        Initialize the parallel processor.
        
        Args:
            max_workers: Maximum number of worker threads/processes (None = auto)
            use_processes: If True, use processes instead of threads
        """
        self.logger = logging.getLogger(__name__)
        
        # Determine number of workers if not specified
        if max_workers is None:
            max_workers = max(1, multiprocessing.cpu_count() - 1)
        
        self.max_workers = max_workers
        self.use_processes = use_processes
        self.logger.info(f"Initialized parallel processor with {max_workers} workers "
                        f"using {'processes' if use_processes else 'threads'}")
    
    def map(self, func: Callable, items: List[Any], timeout: Optional[float] = None) -> List[Any]:
        """
        Apply a function to each item in parallel.
        
        Args:
            func: Function to apply
            items: List of items to process
            timeout: Timeout in seconds for each task
            
        Returns:
            List of results
        """
        if not items:
            return []
        
        executor_class = ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor
        
        with executor_class(max_workers=self.max_workers) as executor:
            if timeout is not None:
                # Use submit and wait with timeout
                futures = [executor.submit(func, item) for item in items]
                results = []
                
                for future in futures:
                    try:
                        result = future.result(timeout=timeout)
                        results.append(result)
                    except TimeoutError:
                        self.logger.warning(f"Task timed out after {timeout} seconds")
                        results.append(None)
                    except Exception as e:
                        self.logger.error(f"Task failed: {e}")
                        results.append(None)
                
                return results
            else:
                # Use map (simpler but no timeout control)
                return list(executor.map(func, items))
    
    def process_files(self, func: Callable[[Path], Any], directory: Union[str, Path], 
                     recursive: bool = True, file_filter: Callable[[Path], bool] = None) -> Dict[Path, Any]:
        """
        Process files in a directory in parallel.
        
        Args:
            func: Function to apply to each file
            directory: Directory to process
            recursive: If True, process subdirectories recursively
            file_filter: Optional function to filter files
            
        Returns:
            Dictionary mapping file paths to results
        """
        directory = Path(directory)
        if not directory.exists() or not directory.is_dir():
            self.logger.error(f"Directory not found: {directory}")
            return {}
        
        # Collect files
        files = []
        if recursive:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    if file_filter is None or file_filter(file_path):
                        files.append(file_path)
        else:
            for file_path in directory.glob("*"):
                if file_path.is_file():
                    if file_filter is None or file_filter(file_path):
                        files.append(file_path)
        
        # Process files in parallel
        results = self.map(func, files)
        
        # Create result dictionary
        return dict(zip(files, results))
    
    def process_chunks(self, func: Callable[[bytes], Any], data: bytes, 
                      chunk_size: int = 1024*1024) -> List[Any]:
        """
        Process large data in chunks in parallel.
        
        Args:
            func: Function to apply to each chunk
            data: Data to process
            chunk_size: Size of each chunk in bytes
            
        Returns:
            List of results for each chunk
        """
        # Split data into chunks
        chunks = []
        for i in range(0, len(data), chunk_size):
            chunks.append(data[i:i+chunk_size])
        
        # Process chunks in parallel
        return self.map(func, chunks)
    
    def throttled_process(self, func: Callable, items: List[Any], 
                         max_items_per_second: int) -> List[Any]:
        """
        Process items with rate limiting.
        
        Args:
            func: Function to apply
            items: List of items to process
            max_items_per_second: Maximum number of items to process per second
            
        Returns:
            List of results
        """
        results = []
        item_queue = queue.Queue()
        result_queue = queue.Queue()
        stop_event = threading.Event()
        
        # Add items to queue
        for item in items:
            item_queue.put(item)
        
        def worker():
            while not stop_event.is_set():
                try:
                    item = item_queue.get(block=False)
                    try:
                        result = func(item)
                        result_queue.put((True, result))
                    except Exception as e:
                        self.logger.error(f"Task failed: {e}")
                        result_queue.put((False, None))
                    finally:
                        item_queue.task_done()
                except queue.Empty:
                    break
                
                # Rate limiting
                if max_items_per_second > 0:
                    time.sleep(1.0 / max_items_per_second)
        
        # Start worker threads
        threads = []
        for _ in range(min(self.max_workers, len(items))):
            thread = threading.Thread(target=worker)
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # Wait for all tasks to complete
        item_queue.join()
        stop_event.set()
        
        # Collect results
        while not result_queue.empty():
            success, result = result_queue.get()
            if success:
                results.append(result)
            else:
                results.append(None)
        
        return results


class IOThrottler:
    """
    Throttles I/O operations to limit system impact.
    """
    
    def __init__(self, max_read_mbps: float = 0, max_write_mbps: float = 0):
        """
        Initialize the I/O throttler.
        
        Args:
            max_read_mbps: Maximum read speed in MB/s (0 = unlimited)
            max_write_mbps: Maximum write speed in MB/s (0 = unlimited)
        """
        self.logger = logging.getLogger(__name__)
        self.max_read_mbps = max_read_mbps
        self.max_write_mbps = max_write_mbps
        
        # Convert to bytes per second
        self.max_read_bps = int(max_read_mbps * 1024 * 1024) if max_read_mbps > 0 else 0
        self.max_write_bps = int(max_write_mbps * 1024 * 1024) if max_write_mbps > 0 else 0
        
        # Tracking variables
        self.read_bytes = 0
        self.write_bytes = 0
        self.last_read_time = time.time()
        self.last_write_time = time.time()
        
        self.logger.info(f"Initialized I/O throttler with max read: {max_read_mbps} MB/s, "
                        f"max write: {max_write_mbps} MB/s")
    
    def throttled_read(self, file_obj: Any, size: int = -1) -> bytes:
        """
        Read from a file with throttling.
        
        Args:
            file_obj: File object to read from
            size: Number of bytes to read
            
        Returns:
            Data read from the file
        """
        if self.max_read_bps <= 0:
            # No throttling
            return file_obj.read(size)
        
        # Check if we need to throttle
        current_time = time.time()
        elapsed = current_time - self.last_read_time
        
        if elapsed > 0 and self.read_bytes > 0:
            current_rate = self.read_bytes / elapsed
            
            if current_rate > self.max_read_bps:
                # Calculate sleep time to achieve target rate
                target_time = self.read_bytes / self.max_read_bps
                sleep_time = max(0, target_time - elapsed)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    # Update elapsed time
                    elapsed = time.time() - self.last_read_time
        
        # Read data
        data = file_obj.read(size)
        
        # Update tracking
        self.read_bytes += len(data)
        
        # Reset counters if too much time has passed
        if elapsed > 1.0:
            self.read_bytes = len(data)
            self.last_read_time = time.time()
        
        return data
    
    def throttled_write(self, file_obj: Any, data: bytes) -> int:
        """
        Write to a file with throttling.
        
        Args:
            file_obj: File object to write to
            data: Data to write
            
        Returns:
            Number of bytes written
        """
        if self.max_write_bps <= 0:
            # No throttling
            return file_obj.write(data)
        
        # Check if we need to throttle
        current_time = time.time()
        elapsed = current_time - self.last_write_time
        
        if elapsed > 0 and self.write_bytes > 0:
            current_rate = self.write_bytes / elapsed
            
            if current_rate > self.max_write_bps:
                # Calculate sleep time to achieve target rate
                target_time = self.write_bytes / self.max_write_bps
                sleep_time = max(0, target_time - elapsed)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    # Update elapsed time
                    elapsed = time.time() - self.last_write_time
        
        # Write data
        bytes_written = file_obj.write(data)
        
        # Update tracking
        self.write_bytes += bytes_written
        
        # Reset counters if too much time has passed
        if elapsed > 1.0:
            self.write_bytes = bytes_written
            self.last_write_time = time.time()
        
        return bytes_written
    
    def throttled_copy(self, src_path: Union[str, Path], dst_path: Union[str, Path], 
                      buffer_size: int = 1024*1024) -> int:
        """
        Copy a file with throttling.
        
        Args:
            src_path: Source file path
            dst_path: Destination file path
            buffer_size: Buffer size for copying
            
        Returns:
            Total bytes copied
        """
        src_path = Path(src_path)
        dst_path = Path(dst_path)
        
        if not src_path.exists():
            raise FileNotFoundError(f"Source file not found: {src_path}")
        
        # Create parent directories if they don't exist
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        
        total_bytes = 0
        
        with open(src_path, 'rb') as src, open(dst_path, 'wb') as dst:
            while True:
                data = self.throttled_read(src, buffer_size)
                if not data:
                    break
                
                bytes_written = self.throttled_write(dst, data)
                total_bytes += bytes_written
        
        return total_bytes


class SmartScheduler:
    """
    Schedules operations during system idle time.
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the smart scheduler.
        
        Args:
            config_path: Path to configuration file
        """
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        
        # Default thresholds
        self.cpu_threshold = self.config.get("smart_scheduling", {}).get("cpu_threshold", 30)
        self.io_threshold = self.config.get("smart_scheduling", {}).get("io_threshold", 50)
        self.memory_threshold = self.config.get("smart_scheduling", {}).get("memory_threshold", 70)
        
        # Quiet hours (e.g., 22:00 - 06:00)
        self.quiet_hours_start = self.config.get("smart_scheduling", {}).get("quiet_hours_start", "22:00")
        self.quiet_hours_end = self.config.get("smart_scheduling", {}).get("quiet_hours_end", "06:00")
        
        self.logger.info(f"Initialized smart scheduler with CPU threshold: {self.cpu_threshold}%, "
                        f"I/O threshold: {self.io_threshold}%, memory threshold: {self.memory_threshold}%")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file."""
        import json
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def is_system_idle(self) -> bool:
        """
        Check if the system is currently idle.
        
        Returns:
            True if the system is idle, False otherwise
        """
        try:
            import psutil
            
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self.cpu_threshold:
                self.logger.debug(f"System not idle: CPU usage {cpu_percent}% > {self.cpu_threshold}%")
                return False
            
            # Check I/O usage
            io_counters = psutil.disk_io_counters()
            if io_counters:
                # This is a simplified check - in a real implementation,
                # you would track I/O rates over time
                io_busy = False
                
                # Check disk I/O for all disks
                for disk, usage in psutil.disk_io_counters(perdisk=True).items():
                    # This is a placeholder - actual implementation would be more sophisticated
                    if disk.startswith(("sd", "hd", "nvme")):
                        io_busy = True
                        break
                
                if io_busy:
                    self.logger.debug(f"System not idle: I/O busy")
                    return False
            
            # Check memory usage
            memory_percent = psutil.virtual_memory().percent
            if memory_percent > self.memory_threshold:
                self.logger.debug(f"System not idle: Memory usage {memory_percent}% > {self.memory_threshold}%")
                return False
            
            # Check if we're in quiet hours
            from datetime import datetime
            now = datetime.now().time()
            start_hour, start_minute = map(int, self.quiet_hours_start.split(":"))
            end_hour, end_minute = map(int, self.quiet_hours_end.split(":"))
            
            start_time = datetime.strptime(self.quiet_hours_start, "%H:%M").time()
            end_time = datetime.strptime(self.quiet_hours_end, "%H:%M").time()
            
            in_quiet_hours = False
            if start_time > end_time:
                # Quiet hours span midnight
                in_quiet_hours = now >= start_time or now <= end_time
            else:
                # Normal time range
                in_quiet_hours = start_time <= now <= end_time
            
            if in_quiet_hours:
                self.logger.debug("System idle: In quiet hours")
                return True
            
            self.logger.debug("System idle: All checks passed")
            return True
        
        except ImportError:
            self.logger.warning("psutil not installed, cannot check system idle state")
            return True
        except Exception as e:
            self.logger.error(f"Error checking system idle state: {e}")
            return True
    
    def wait_for_idle(self, timeout: Optional[float] = None) -> bool:
        """
        Wait until the system is idle.
        
        Args:
            timeout: Maximum time to wait in seconds (None = wait indefinitely)
            
        Returns:
            True if the system became idle, False if timeout was reached
        """
        start_time = time.time()
        
        while True:
            if self.is_system_idle():
                return True
            
            if timeout is not None and time.time() - start_time > timeout:
                self.logger.warning(f"Timeout reached while waiting for system idle")
                return False
            
            # Wait before checking again
            time.sleep(5)
    
    def run_when_idle(self, func: Callable, *args, timeout: Optional[float] = None, **kwargs) -> Any:
        """
        Run a function when the system is idle.
        
        Args:
            func: Function to run
            *args: Arguments to pass to the function
            timeout: Maximum time to wait for idle state in seconds
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Result of the function or None if timeout was reached
        """
        if self.wait_for_idle(timeout):
            self.logger.info(f"Running {func.__name__} during idle time")
            return func(*args, **kwargs)
        else:
            self.logger.warning(f"Could not run {func.__name__} during idle time (timeout)")
            return None