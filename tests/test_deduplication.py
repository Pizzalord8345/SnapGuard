#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import unittest
import tempfile
import json
import shutil
import hashlib
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from deduplication import DeduplicationManager

class TestDeduplication(unittest.TestCase):
    """Test cases for the DeduplicationManager class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create a test config file
        self.config_path = os.path.join(self.test_dir, "test_config.json")
        self.dedup_dir = os.path.join(self.test_dir, "dedup")
        
        config = {
            "storage": {
                "deduplication_directory": self.dedup_dir,
                "deduplication": {
                    "enabled": True,
                    "method": "file",
                    "block_size": 4096
                }
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f)
        
        # Create a test snapshot directory
        self.snapshot_dir = os.path.join(self.test_dir, "snapshot")
        os.makedirs(self.snapshot_dir)
        
        # Create some test files with duplicate content
        self.create_test_files()
        
        # Create deduplication manager instance
        self.dedup_manager = DeduplicationManager(self.config_path)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
    
    def create_test_files(self):
        """Create test files for deduplication testing."""
        # Create a few files with the same content
        content1 = b"This is test content for deduplication testing."
        content2 = b"This is different content for testing deduplication."
        
        # Create files with content1
        for i in range(3):
            file_path = os.path.join(self.snapshot_dir, f"file{i+1}.txt")
            with open(file_path, 'wb') as f:
                f.write(content1)
        
        # Create files with content2
        for i in range(2):
            file_path = os.path.join(self.snapshot_dir, f"different{i+1}.txt")
            with open(file_path, 'wb') as f:
                f.write(content2)
        
        # Create a subdirectory with duplicate files
        subdir = os.path.join(self.snapshot_dir, "subdir")
        os.makedirs(subdir)
        
        # Create duplicate files in subdirectory
        with open(os.path.join(subdir, "duplicate1.txt"), 'wb') as f:
            f.write(content1)
        
        with open(os.path.join(subdir, "duplicate2.txt"), 'wb') as f:
            f.write(content2)
    
    def test_file_deduplication(self):
        """Test file-level deduplication."""
        # Run deduplication
        stats = self.dedup_manager.deduplicate_snapshot(self.snapshot_dir)
        
        # Check that deduplication was successful
        self.assertIsNotNone(stats)
        self.assertNotIn("error", stats)
        
        # Check that files were deduplicated
        self.assertGreater(stats["files_deduplicated"], 0)
        self.assertGreater(stats["space_saved"], 0)
        
        # Check that metadata file was created
        metadata_file = os.path.join(self.snapshot_dir, ".deduplication_metadata.json")
        self.assertTrue(os.path.exists(metadata_file))
        
        # Check that deduplication index was updated
        index = self.dedup_manager._load_dedup_index()
        self.assertGreater(len(index["file_hashes"]), 0)
        
        # Check that some files were replaced with links
        # In a real implementation, we would check for hard links or symbolic links
        # For this test, we'll just check that the files still exist
        self.assertTrue(os.path.exists(os.path.join(self.snapshot_dir, "file1.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.snapshot_dir, "file2.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.snapshot_dir, "file3.txt")))
    
    def test_block_deduplication(self):
        """Test block-level deduplication."""
        # Change deduplication method to block
        self.dedup_manager.config["storage"]["deduplication"]["method"] = "block"
        
        # Run deduplication
        stats = self.dedup_manager.deduplicate_snapshot(self.snapshot_dir)
        
        # Check that deduplication was successful
        self.assertIsNotNone(stats)
        self.assertNotIn("error", stats)
        
        # Check that blocks were deduplicated
        self.assertGreater(stats["blocks_deduplicated"], 0)
        self.assertGreater(stats["space_saved"], 0)
        
        # Check that metadata file was created
        metadata_file = os.path.join(self.snapshot_dir, ".deduplication_metadata.json")
        self.assertTrue(os.path.exists(metadata_file))
        
        # Check that block map files were created
        block_maps_exist = False
        for root, dirs, files in os.walk(self.dedup_manager.config["storage"]["deduplication_directory"]):
            for file in files:
                if file.endswith(".blockmap"):
                    block_maps_exist = True
                    break
            if block_maps_exist:
                break
        
        self.assertTrue(block_maps_exist)
    
    def test_restore_deduplicated_snapshot(self):
        """Test restoring a deduplicated snapshot."""
        # Run deduplication
        self.dedup_manager.deduplicate_snapshot(self.snapshot_dir)
        
        # Restore the snapshot
        restore_stats = self.dedup_manager.restore_deduplicated_snapshot(self.snapshot_dir)
        
        # Check that restoration was successful
        self.assertIsNotNone(restore_stats)
        self.assertNotIn("error", restore_stats)
        
        # Check that files were restored
        self.assertGreater(restore_stats["files_restored"], 0)
        
        # Check that metadata file was removed
        metadata_file = os.path.join(self.snapshot_dir, ".deduplication_metadata.json")
        self.assertFalse(os.path.exists(metadata_file))
        
        # Check that all files exist and have correct content
        content1 = b"This is test content for deduplication testing."
        content2 = b"This is different content for testing deduplication."
        
        # Check files with content1
        for i in range(3):
            file_path = os.path.join(self.snapshot_dir, f"file{i+1}.txt")
            with open(file_path, 'rb') as f:
                self.assertEqual(f.read(), content1)
        
        # Check files with content2
        for i in range(2):
            file_path = os.path.join(self.snapshot_dir, f"different{i+1}.txt")
            with open(file_path, 'rb') as f:
                self.assertEqual(f.read(), content2)
        
        # Check subdirectory files
        with open(os.path.join(self.snapshot_dir, "subdir", "duplicate1.txt"), 'rb') as f:
            self.assertEqual(f.read(), content1)
        
        with open(os.path.join(self.snapshot_dir, "subdir", "duplicate2.txt"), 'rb') as f:
            self.assertEqual(f.read(), content2)
    
    def test_get_deduplication_stats(self):
        """Test getting deduplication statistics."""
        # Run deduplication
        self.dedup_manager.deduplicate_snapshot(self.snapshot_dir)
        
        # Get statistics
        stats = self.dedup_manager.get_deduplication_stats()
        
        # Check that statistics are returned
        self.assertIsNotNone(stats)
        self.assertIn("total_files", stats)
        self.assertIn("deduplicated_files", stats)
        self.assertIn("space_saved", stats)
        
        # Check that statistics are reasonable
        self.assertGreater(stats["total_files"], 0)
        self.assertGreaterEqual(stats["deduplicated_files"], 0)
        self.assertGreaterEqual(stats["space_saved"], 0)
    
    def test_cleanup_orphaned_blocks(self):
        """Test cleaning up orphaned blocks."""
        # Change deduplication method to block
        self.dedup_manager.config["storage"]["deduplication"]["method"] = "block"
        
        # Run deduplication
        self.dedup_manager.deduplicate_snapshot(self.snapshot_dir)
        
        # Get initial block count
        index = self.dedup_manager._load_dedup_index()
        initial_block_count = len(index["block_hashes"])
        
        # Mark some blocks as orphaned (references = 0)
        block_hash = next(iter(index["block_hashes"]))
        index["block_hashes"][block_hash]["references"] = 0
        self.dedup_manager._save_dedup_index(index)
        
        # Clean up orphaned blocks
        removed_count = self.dedup_manager.cleanup_orphaned_blocks()
        
        # Check that blocks were removed
        self.assertEqual(removed_count, 1)
        
        # Check that block was removed from index
        index = self.dedup_manager._load_dedup_index()
        self.assertEqual(len(index["block_hashes"]), initial_block_count - 1)
        self.assertNotIn(block_hash, index["block_hashes"])

if __name__ == '__main__':
    unittest.main()