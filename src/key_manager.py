#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
import time
import base64
import secrets
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta

# Cryptography imports
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305

# For system keyring integration
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

class KeyManager:
    """
    Advanced key management system for SnapGuard.
    Handles key generation, rotation, storage, and retrieval.
    """
    
    KEY_TYPES = ["encryption", "signing", "master", "recovery"]
    STORAGE_BACKENDS = ["file", "keyring"]
    ENCRYPTION_ALGORITHMS = ["aes-256-gcm", "chacha20-poly1305"]
    
    def __init__(self, config_path: str = "config.json"):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        self.keys = {}
        self.key_metadata = {}
        self._initialize_key_storage()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file."""
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def _initialize_key_storage(self) -> None:
        """Initialize key storage directories and metadata."""
        # Create key storage directory if it doesn't exist
        key_dir = Path(self.config['security']['key_directory'])
        key_dir.mkdir(parents=True, exist_ok=True)
        
        # Create metadata file if it doesn't exist
        metadata_file = key_dir / "key_metadata.json"
        if not metadata_file.exists():
            default_metadata = {
                "created": datetime.now().isoformat(),
                "last_rotation": None,
                "keys": {}
            }
            with open(metadata_file, 'w') as f:
                json.dump(default_metadata, f, indent=2)
        
        # Load metadata
        with open(metadata_file, 'r') as f:
            self.key_metadata = json.load(f)
    
    def _save_key_metadata(self) -> None:
        """Save key metadata to file."""
        key_dir = Path(self.config['security']['key_directory'])
        metadata_file = key_dir / "key_metadata.json"
        
        with open(metadata_file, 'w') as f:
            json.dump(self.key_metadata, f, indent=2)
    
    def generate_key(self, key_type: str, algorithm: str = "aes-256-gcm", 
                    storage_backend: str = "file", description: str = "") -> str:
        """
        Generate a new key of the specified type.
        
        Args:
            key_type: Type of key (encryption, signing, master, recovery)
            algorithm: Encryption algorithm to use
            storage_backend: Where to store the key (file, keyring)
            description: Human-readable description of the key
            
        Returns:
            Key ID of the generated key
        """
        if key_type not in self.KEY_TYPES:
            raise ValueError(f"Invalid key type: {key_type}")
        
        if algorithm not in self.ENCRYPTION_ALGORITHMS and key_type == "encryption":
            raise ValueError(f"Invalid encryption algorithm: {algorithm}")
        
        if storage_backend not in self.STORAGE_BACKENDS:
            raise ValueError(f"Invalid storage backend: {storage_backend}")
        
        # Generate a unique key ID
        key_id = f"{key_type}_{int(time.time())}_{secrets.token_hex(4)}"
        
        # Generate key material based on algorithm
        if algorithm == "aes-256-gcm":
            key_material = AESGCM.generate_key(bit_length=256)
        elif algorithm == "chacha20-poly1305":
            key_material = ChaCha20Poly1305.generate_key()
        else:
            # For signing and other keys, use 32 bytes of random data
            key_material = os.urandom(32)
        
        # Store the key using the specified backend
        self._store_key(key_id, key_material, storage_backend)
        
        # Update metadata
        if key_type not in self.key_metadata["keys"]:
            self.key_metadata["keys"][key_type] = []
        
        self.key_metadata["keys"][key_type].append({
            "id": key_id,
            "algorithm": algorithm,
            "storage": storage_backend,
            "description": description,
            "created": datetime.now().isoformat(),
            "last_used": None,
            "active": True
        })
        
        self._save_key_metadata()
        self.logger.info(f"Generated new {key_type} key: {key_id}")
        
        return key_id
    
    def _store_key(self, key_id: str, key_material: bytes, storage_backend: str) -> None:
        """Store a key using the specified backend."""
        if storage_backend == "file":
            key_dir = Path(self.config['security']['key_directory'])
            key_file = key_dir / f"{key_id}.key"
            
            with open(key_file, 'wb') as f:
                f.write(key_material)
                
        elif storage_backend == "keyring" and KEYRING_AVAILABLE:
            # Store in system keyring
            keyring.set_password("snapguard", key_id, base64.b64encode(key_material).decode())
        else:
            raise ValueError(f"Unsupported storage backend: {storage_backend}")
    
    def get_key(self, key_id: str) -> bytes:
        """Retrieve a key by its ID."""
        # Check if key is already loaded in memory
        if key_id in self.keys:
            return self.keys[key_id]
        
        # Find key metadata
        key_metadata = None
        key_type = None
        
        for ktype, keys in self.key_metadata["keys"].items():
            for key in keys:
                if key["id"] == key_id:
                    key_metadata = key
                    key_type = ktype
                    break
            if key_metadata:
                break
        
        if not key_metadata:
            raise ValueError(f"Key not found: {key_id}")
        
        # Retrieve key from storage
        storage = key_metadata["storage"]
        
        if storage == "file":
            key_dir = Path(self.config['security']['key_directory'])
            key_file = key_dir / f"{key_id}.key"
            
            if not key_file.exists():
                raise FileNotFoundError(f"Key file not found: {key_file}")
            
            with open(key_file, 'rb') as f:
                key_material = f.read()
                
        elif storage == "keyring" and KEYRING_AVAILABLE:
            # Retrieve from system keyring
            encoded_key = keyring.get_password("snapguard", key_id)
            if not encoded_key:
                raise ValueError(f"Key not found in keyring: {key_id}")
            key_material = base64.b64decode(encoded_key)
        else:
            raise ValueError(f"Unsupported storage backend: {storage}")
        
        # Update last used timestamp
        for key in self.key_metadata["keys"][key_type]:
            if key["id"] == key_id:
                key["last_used"] = datetime.now().isoformat()
                break
        
        self._save_key_metadata()
        
        # Cache key in memory
        self.keys[key_id] = key_material
        
        return key_material
    
    def get_active_key(self, key_type: str) -> Tuple[str, bytes]:
        """Get the currently active key of the specified type."""
        if key_type not in self.key_metadata["keys"]:
            raise ValueError(f"No keys found for type: {key_type}")
        
        # Find the active key
        active_keys = [k for k in self.key_metadata["keys"][key_type] if k.get("active", False)]
        
        if not active_keys:
            raise ValueError(f"No active keys found for type: {key_type}")
        
        # Use the most recently created active key
        active_key = sorted(active_keys, key=lambda k: k["created"], reverse=True)[0]
        key_id = active_key["id"]
        
        # Get the key material
        key_material = self.get_key(key_id)
        
        return key_id, key_material
    
    def rotate_keys(self, key_type: str = None) -> Dict:
        """
        Rotate keys of the specified type or all keys if type is None.
        
        Returns:
            Dictionary with old and new key IDs
        """
        result = {}
        
        if key_type is None:
            # Rotate all key types
            for kt in self.KEY_TYPES:
                if kt in self.key_metadata["keys"] and self.key_metadata["keys"][kt]:
                    result[kt] = self._rotate_key_type(kt)
        else:
            # Rotate specific key type
            if key_type not in self.key_metadata["keys"] or not self.key_metadata["keys"][key_type]:
                raise ValueError(f"No keys found for type: {key_type}")
            
            result[key_type] = self._rotate_key_type(key_type)
        
        # Update last rotation timestamp
        self.key_metadata["last_rotation"] = datetime.now().isoformat()
        self._save_key_metadata()
        
        return result
    
    def _rotate_key_type(self, key_type: str) -> Dict:
        """Rotate keys of a specific type."""
        # Get current active key
        active_keys = [k for k in self.key_metadata["keys"][key_type] if k.get("active", False)]
        
        if not active_keys:
            raise ValueError(f"No active keys found for type: {key_type}")
        
        old_key = sorted(active_keys, key=lambda k: k["created"], reverse=True)[0]
        old_key_id = old_key["id"]
        
        # Generate new key with same parameters
        algorithm = old_key.get("algorithm", "aes-256-gcm")
        storage = old_key.get("storage", "file")
        description = f"Rotated from {old_key_id} on {datetime.now().isoformat()}"
        
        new_key_id = self.generate_key(key_type, algorithm, storage, description)
        
        # Deactivate old key
        for key in self.key_metadata["keys"][key_type]:
            if key["id"] == old_key_id:
                key["active"] = False
                key["deactivated"] = datetime.now().isoformat()
                break
        
        self._save_key_metadata()
        self.logger.info(f"Rotated {key_type} key: {old_key_id} -> {new_key_id}")
        
        return {
            "old_key_id": old_key_id,
            "new_key_id": new_key_id
        }
    
    def should_rotate_keys(self) -> List[str]:
        """
        Check if any keys should be rotated based on age or usage.
        
        Returns:
            List of key types that should be rotated
        """
        rotation_needed = []
        now = datetime.now()
        
        # Check rotation policy from config
        rotation_policy = self.config.get("security", {}).get("key_rotation", {})
        max_age_days = rotation_policy.get("max_age_days", 90)
        
        for key_type, keys in self.key_metadata["keys"].items():
            active_keys = [k for k in keys if k.get("active", False)]
            
            if not active_keys:
                continue
            
            # Get the most recently created active key
            active_key = sorted(active_keys, key=lambda k: k["created"], reverse=True)[0]
            
            # Check if key is too old
            created = datetime.fromisoformat(active_key["created"])
            age_days = (now - created).days
            
            if age_days > max_age_days:
                rotation_needed.append(key_type)
                self.logger.info(f"Key rotation needed for {key_type}: age is {age_days} days")
        
        return rotation_needed
    
    def cleanup_old_keys(self, retention_days: int = 180) -> int:
        """
        Remove old, inactive keys that are beyond the retention period.
        
        Args:
            retention_days: Number of days to keep inactive keys
            
        Returns:
            Number of keys removed
        """
        removed_count = 0
        now = datetime.now()
        cutoff_date = now - timedelta(days=retention_days)
        
        for key_type, keys in list(self.key_metadata["keys"].items()):
            for key in list(keys):
                # Skip active keys
                if key.get("active", False):
                    continue
                
                # Check if key was deactivated
                if "deactivated" in key:
                    deactivated = datetime.fromisoformat(key["deactivated"])
                    if deactivated < cutoff_date:
                        # Remove the key
                        self._remove_key(key["id"], key.get("storage", "file"))
                        keys.remove(key)
                        removed_count += 1
                        self.logger.info(f"Removed old key: {key['id']}")
        
        if removed_count > 0:
            self._save_key_metadata()
        
        return removed_count
    
    def _remove_key(self, key_id: str, storage: str) -> None:
        """Remove a key from storage."""
        if storage == "file":
            key_dir = Path(self.config['security']['key_directory'])
            key_file = key_dir / f"{key_id}.key"
            
            if key_file.exists():
                key_file.unlink()
                
        elif storage == "keyring" and KEYRING_AVAILABLE:
            # Remove from system keyring
            keyring.delete_password("snapguard", key_id)
            
        # Remove from memory cache if present
        if key_id in self.keys:
            del self.keys[key_id]