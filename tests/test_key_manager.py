#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import unittest
import tempfile
import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from key_manager import KeyManager

class TestKeyManager(unittest.TestCase):
    """Test cases for the KeyManager class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create a test config file
        self.config_path = os.path.join(self.test_dir, "test_config.json")
        self.key_dir = os.path.join(self.test_dir, "keys")
        
        config = {
            "security": {
                "key_directory": self.key_dir,
                "encryption": {
                    "enabled": True,
                    "algorithm": "aes-256-gcm",
                    "key_file": os.path.join(self.key_dir, "encryption.key")
                },
                "signing": {
                    "enabled": True,
                    "key_file": os.path.join(self.key_dir, "signing.key")
                },
                "key_rotation": {
                    "enabled": True,
                    "max_age_days": 90,
                    "auto_rotate": True
                }
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f)
        
        # Create key manager instance
        self.key_manager = KeyManager(self.config_path)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
    
    def test_generate_key(self):
        """Test generating a new key."""
        # Generate a key
        key_id = self.key_manager.generate_key("encryption", "aes-256-gcm", "file", "Test key")
        
        # Check that key ID is returned
        self.assertIsNotNone(key_id)
        self.assertTrue(key_id.startswith("encryption_"))
        
        # Check that key file was created
        key_file = os.path.join(self.key_dir, f"{key_id}.key")
        self.assertTrue(os.path.exists(key_file))
        
        # Check that key metadata was updated
        self.assertIn("encryption", self.key_manager.key_metadata["keys"])
        self.assertIn(key_id, [k["id"] for k in self.key_manager.key_metadata["keys"]["encryption"]])
    
    def test_get_key(self):
        """Test retrieving a key."""
        # Generate a key
        key_id = self.key_manager.generate_key("encryption", "aes-256-gcm")
        
        # Get the key
        key_material = self.key_manager.get_key(key_id)
        
        # Check that key material is returned
        self.assertIsNotNone(key_material)
        self.assertEqual(len(key_material), 32)  # AES-256 key is 32 bytes
    
    def test_get_active_key(self):
        """Test getting the active key of a specific type."""
        # Generate multiple keys
        key_id1 = self.key_manager.generate_key("signing", "aes-256-gcm")
        key_id2 = self.key_manager.generate_key("signing", "aes-256-gcm")
        
        # Get active key
        active_key_id, active_key = self.key_manager.get_active_key("signing")
        
        # Check that the most recently created key is active
        self.assertEqual(active_key_id, key_id2)
        self.assertIsNotNone(active_key)
    
    def test_rotate_keys(self):
        """Test key rotation."""
        # Generate initial key
        old_key_id = self.key_manager.generate_key("encryption", "aes-256-gcm")
        
        # Rotate keys
        result = self.key_manager.rotate_keys("encryption")
        
        # Check rotation result
        self.assertIn("encryption", result)
        self.assertEqual(result["encryption"]["old_key_id"], old_key_id)
        new_key_id = result["encryption"]["new_key_id"]
        
        # Check that new key is active and old key is inactive
        for key in self.key_manager.key_metadata["keys"]["encryption"]:
            if key["id"] == old_key_id:
                self.assertFalse(key["active"])
                self.assertIn("deactivated", key)
            elif key["id"] == new_key_id:
                self.assertTrue(key["active"])
    
    def test_should_rotate_keys(self):
        """Test checking if keys should be rotated."""
        # Generate a key
        key_id = self.key_manager.generate_key("encryption", "aes-256-gcm")
        
        # Modify key creation date to be old
        for key in self.key_manager.key_metadata["keys"]["encryption"]:
            if key["id"] == key_id:
                # Set creation date to 100 days ago
                old_date = datetime.now() - timedelta(days=100)
                key["created"] = old_date.isoformat()
        
        # Save metadata
        self.key_manager._save_key_metadata()
        
        # Check if keys should be rotated
        rotation_needed = self.key_manager.should_rotate_keys()
        
        # Encryption key should need rotation (older than 90 days)
        self.assertIn("encryption", rotation_needed)
    
    def test_cleanup_old_keys(self):
        """Test cleaning up old keys."""
        # Generate keys
        key_id1 = self.key_manager.generate_key("encryption", "aes-256-gcm")
        key_id2 = self.key_manager.generate_key("encryption", "aes-256-gcm")
        
        # Deactivate first key
        for key in self.key_manager.key_metadata["keys"]["encryption"]:
            if key["id"] == key_id1:
                key["active"] = False
                # Set deactivation date to 200 days ago
                old_date = datetime.now() - timedelta(days=200)
                key["deactivated"] = old_date.isoformat()
        
        # Save metadata
        self.key_manager._save_key_metadata()
        
        # Clean up old keys (retention = 180 days)
        removed_count = self.key_manager.cleanup_old_keys(180)
        
        # One key should be removed
        self.assertEqual(removed_count, 1)
        
        # Check that key1 was removed and key2 still exists
        remaining_keys = [k["id"] for k in self.key_manager.key_metadata["keys"]["encryption"]]
        self.assertNotIn(key_id1, remaining_keys)
        self.assertIn(key_id2, remaining_keys)
    
    def test_different_key_types(self):
        """Test generating different types of keys."""
        # Generate keys of different types
        encryption_key_id = self.key_manager.generate_key("encryption", "aes-256-gcm")
        signing_key_id = self.key_manager.generate_key("signing")
        master_key_id = self.key_manager.generate_key("master")
        recovery_key_id = self.key_manager.generate_key("recovery")
        
        # Check that all keys were created
        self.assertIsNotNone(encryption_key_id)
        self.assertIsNotNone(signing_key_id)
        self.assertIsNotNone(master_key_id)
        self.assertIsNotNone(recovery_key_id)
        
        # Check that keys are of different types
        self.assertTrue(encryption_key_id.startswith("encryption_"))
        self.assertTrue(signing_key_id.startswith("signing_"))
        self.assertTrue(master_key_id.startswith("master_"))
        self.assertTrue(recovery_key_id.startswith("recovery_"))
    
    def test_chacha20_poly1305_algorithm(self):
        """Test generating a key with ChaCha20-Poly1305 algorithm."""
        # Generate a key with ChaCha20-Poly1305
        key_id = self.key_manager.generate_key("encryption", "chacha20-poly1305")
        
        # Check that key was created
        self.assertIsNotNone(key_id)
        
        # Check that algorithm was saved in metadata
        for key in self.key_manager.key_metadata["keys"]["encryption"]:
            if key["id"] == key_id:
                self.assertEqual(key["algorithm"], "chacha20-poly1305")

if __name__ == '__main__':
    unittest.main()