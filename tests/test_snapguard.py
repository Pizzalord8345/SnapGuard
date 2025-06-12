import unittest
import os
import sys
from pathlib import Path
import json
import hashlib
import hmac
import base64
import tempfile
import shutil

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from snapguard import SnapGuard
from cryptography.fernet import Fernet

class TestSnapGuard(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_path = Path(self.test_dir) / "config.json"
        self.snapshot_location = Path(self.test_dir) / "snapshots"
        self.snapshot_location.mkdir(parents=True, exist_ok=True)

        self.enc_key_file = Path(self.test_dir) / "enc.key"
        self.sign_key_file = Path(self.test_dir) / "sign.key"
        # Salt file will be enc_key_file.salt

        self.config_data = {
            "security": {
                "encryption": {
                    "enabled": True,
                    "key_file": str(self.enc_key_file),
                    "algorithm": "fernet" # Example, adjust if your config uses it
                },
                "signing": {
                    "enabled": True,
                    "key_file": str(self.sign_key_file)
                },
                "audit_log": str(Path(self.test_dir) / "audit.log")
            },
            "snapshot": {
                "default_location": str(self.snapshot_location),
                "subvolumes": [], # Keep it simple for these tests
                "retention": {}, # Keep it simple
                "schedule": {} # Keep it simple
            },
            "logging": { # Add basic logging config to avoid errors if SnapGuard tries to use it
                "enabled": False,
                "journald": False,
                "level": "INFO"
            },
            "notifications": { # Add basic notifications config
                "enabled": False
            },
            "backup": { # Add basic backup config
                 "enabled": False
            }
        }

        with open(self.config_path, 'w') as f:
            json.dump(self.config_data, f)

        self.snapguard = SnapGuard(config_path=str(self.config_path))
        # SnapGuard constructor calls _setup_encryption and _setup_signing,
        # which in turn call _generate_encryption_key and _generate_signing_key
        # if keys don't exist. So keys (and salt) should be generated here.

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_generate_keys_permissions(self):
        # Keys and salt are generated in setUp via SnapGuard constructor
        self.assertTrue(self.enc_key_file.exists())
        self.assertTrue(self.sign_key_file.exists())

        salt_file = self.enc_key_file.with_suffix('.salt')
        self.assertTrue(salt_file.exists())

        # Check permissions (stat().st_mode returns a complex number, need to mask)
        # Expected: -rw------- which is 0o600 for the user.
        # os.stat().st_mode gives 0o100600 for a regular file.
        expected_permissions = 0o100600
        self.assertEqual(os.stat(self.enc_key_file).st_mode & 0o777777, expected_permissions)
        self.assertEqual(os.stat(self.sign_key_file).st_mode & 0o777777, expected_permissions)
        self.assertEqual(os.stat(salt_file).st_mode & 0o777777, expected_permissions)

    def test_encrypt_decrypt_snapshot_data(self):
        dummy_snapshot_name = "test_snap_1"
        dummy_snapshot_path = self.snapshot_location / dummy_snapshot_name
        dummy_snapshot_path.mkdir()

        file1_path = dummy_snapshot_path / "file1.txt"
        file2_path = dummy_snapshot_path / "subdir" / "file2.txt"
        file2_path.parent.mkdir()

        original_content1 = b"This is test content for file 1."
        original_content2 = b"Another test content for file 2, with some more data."

        with open(file1_path, 'wb') as f:
            f.write(original_content1)
        with open(file2_path, 'wb') as f:
            f.write(original_content2)

        # Encrypt
        self.assertTrue(self.snapguard._encrypt_snapshot(str(dummy_snapshot_path)))

        encryption_metadata_file = dummy_snapshot_path / ".encryption_metadata.json"
        self.assertTrue(encryption_metadata_file.exists())

        # Verify content changed (is encrypted)
        with open(file1_path, 'rb') as f:
            encrypted_content1 = f.read()
        with open(file2_path, 'rb') as f:
            encrypted_content2 = f.read()

        self.assertNotEqual(original_content1, encrypted_content1)
        self.assertNotEqual(original_content2, encrypted_content2)

        # Attempt to decrypt with original Fernet key to prove it's valid encryption
        # This is an indirect way to check if encryption_key was set up correctly
        f_test = Fernet(self.snapguard.encryption_key)
        self.assertEqual(original_content1, f_test.decrypt(encrypted_content1))
        self.assertEqual(original_content2, f_test.decrypt(encrypted_content2))


        # Decrypt
        self.assertTrue(self.snapguard._decrypt_snapshot(str(dummy_snapshot_path)))

        # For this test, we expect .encryption_metadata.json to be removed
        self.assertFalse(encryption_metadata_file.exists())

        # Verify content restored
        with open(file1_path, 'rb') as f:
            decrypted_content1 = f.read()
        with open(file2_path, 'rb') as f:
            decrypted_content2 = f.read()

        self.assertEqual(original_content1, decrypted_content1)
        self.assertEqual(original_content2, decrypted_content2)

if __name__ == '__main__':
    unittest.main()
