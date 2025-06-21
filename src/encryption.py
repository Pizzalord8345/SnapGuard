#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
import base64
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from cryptography.hazmat.primitives.hmac import HMAC

class EncryptionManager:
    """
    Enhanced encryption manager for SnapGuard.
    Supports multiple encryption algorithms and selective file encryption.
    """
    
    SUPPORTED_ALGORITHMS = {
        "aes-256-gcm": {
            "class": AESGCM,
            "key_size": 32,  # 256 bits
            "description": "AES-256 in Galois/Counter Mode"
        },
        "chacha20-poly1305": {
            "class": ChaCha20Poly1305,
            "key_size": 32,  # 256 bits
            "description": "ChaCha20-Poly1305 AEAD"
        }
    }
    
    def __init__(self, key_manager, config):
        self.logger = logging.getLogger(__name__)
        self.key_manager = key_manager
        self.config = config
        
    def encrypt_file(self, file_path: Union[str, Path], algorithm: str = None) -> bool:
        """
        Encrypt a single file using the specified algorithm.
        
        Args:
            file_path: Path to the file to encrypt
            algorithm: Encryption algorithm to use (defaults to config setting)
            
        Returns:
            True if encryption was successful, False otherwise
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists() or not file_path.is_file():
                self.logger.error(f"File not found or not a regular file: {file_path}")
                return False
            
            # Use specified algorithm or default from config
            if algorithm is None:
                algorithm = self.config['security']['encryption']['algorithm']
            
            if algorithm not in self.SUPPORTED_ALGORITHMS:
                self.logger.error(f"Unsupported encryption algorithm: {algorithm}")
                return False
            
            # Get the active encryption key
            key_id, key_material = self.key_manager.get_active_key("encryption")
            
            # Read the file content
            with open(file_path, 'rb') as f:
                plaintext = f.read()
            
            # Generate a random nonce/IV
            if algorithm == "aes-256-gcm":
                cipher = AESGCM(key_material)
                nonce = os.urandom(12)  # 96 bits for GCM
                ciphertext = cipher.encrypt(nonce, plaintext, None)
            elif algorithm == "chacha20-poly1305":
                cipher = ChaCha20Poly1305(key_material)
                nonce = os.urandom(12)  # 96 bits for ChaCha20-Poly1305
                ciphertext = cipher.encrypt(nonce, plaintext, None)
            
            # Create metadata
            metadata = {
                "algorithm": algorithm,
                "key_id": key_id,
                "nonce": base64.b64encode(nonce).decode(),
                "encrypted": True
            }
            
            # Write encrypted data and metadata
            encrypted_data = {
                "metadata": metadata,
                "data": base64.b64encode(ciphertext).decode()
            }
            
            with open(file_path, 'w') as f:
                json.dump(encrypted_data, f)
            
            return True
        except Exception as e:
            self.logger.error(f"Error encrypting file {file_path}: {e}")
            return False
    
    def decrypt_file(self, file_path: Union[str, Path]) -> bool:
        """
        Decrypt a single file.
        
        Args:
            file_path: Path to the encrypted file
            
        Returns:
            True if decryption was successful, False otherwise
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists() or not file_path.is_file():
                self.logger.error(f"File not found or not a regular file: {file_path}")
                return False
            
            # Read the encrypted file
            with open(file_path, 'r') as f:
                try:
                    encrypted_data = json.load(f)
                except json.JSONDecodeError:
                    self.logger.error(f"File is not in the expected encrypted format: {file_path}")
                    return False
            
            if "metadata" not in encrypted_data or "data" not in encrypted_data:
                self.logger.error(f"Invalid encrypted file format: {file_path}")
                return False
            
            metadata = encrypted_data["metadata"]
            if not metadata.get("encrypted", False):
                self.logger.error(f"File is not marked as encrypted: {file_path}")
                return False
            
            # Get the encryption key
            key_id = metadata["key_id"]
            try:
                key_material = self.key_manager.get_key(key_id)
            except ValueError:
                self.logger.error(f"Encryption key not found: {key_id}")
                return False
            
            # Get the algorithm and nonce
            algorithm = metadata["algorithm"]
            nonce = base64.b64decode(metadata["nonce"])
            
            # Decode the ciphertext
            ciphertext = base64.b64decode(encrypted_data["data"])
            
            # Decrypt the data
            if algorithm == "aes-256-gcm":
                cipher = AESGCM(key_material)
                plaintext = cipher.decrypt(nonce, ciphertext, None)
            elif algorithm == "chacha20-poly1305":
                cipher = ChaCha20Poly1305(key_material)
                plaintext = cipher.decrypt(nonce, ciphertext, None)
            else:
                self.logger.error(f"Unsupported encryption algorithm: {algorithm}")
                return False
            
            # Write the decrypted data back to the file
            with open(file_path, 'wb') as f:
                f.write(plaintext)
            
            return True
        except Exception as e:
            self.logger.error(f"Error decrypting file {file_path}: {e}")
            return False
    
    def encrypt_directory(self, directory_path: Union[str, Path], 
                         algorithm: str = None, 
                         selective: bool = False,
                         patterns: List[str] = None) -> Tuple[int, int]:
        """
        Encrypt files in a directory, with optional selective encryption.
        
        Args:
            directory_path: Path to the directory
            algorithm: Encryption algorithm to use
            selective: If True, only encrypt files matching patterns
            patterns: List of glob patterns for selective encryption
            
        Returns:
            Tuple of (success_count, failure_count)
        """
        directory_path = Path(directory_path)
        if not directory_path.exists() or not directory_path.is_dir():
            self.logger.error(f"Directory not found: {directory_path}")
            return (0, 0)
        
        success_count = 0
        failure_count = 0
        
        # Create a metadata file for the directory
        metadata_file = directory_path / ".encryption_metadata.json"
        metadata = {
            "encrypted_at": str(datetime.datetime.now()),
            "algorithm": algorithm or self.config['security']['encryption']['algorithm'],
            "selective": selective,
            "patterns": patterns,
            "encrypted_files": []
        }
        
        # Process all files in the directory
        for file_path in directory_path.rglob("*"):
            if not file_path.is_file() or file_path.name == ".encryption_metadata.json":
                continue
            
            # Check if we should encrypt this file
            should_encrypt = not selective
            if selective and patterns:
                for pattern in patterns:
                    if file_path.match(pattern):
                        should_encrypt = True
                        break
            
            if should_encrypt:
                if self.encrypt_file(file_path, algorithm):
                    success_count += 1
                    metadata["encrypted_files"].append(str(file_path.relative_to(directory_path)))
                else:
                    failure_count += 1
        
        # Save the metadata
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.logger.info(f"Encrypted {success_count} files in {directory_path} "
                        f"({failure_count} failures)")
        
        return (success_count, failure_count)
    
    def decrypt_directory(self, directory_path: Union[str, Path]) -> Tuple[int, int]:
        """
        Decrypt files in a directory based on the metadata.
        
        Args:
            directory_path: Path to the encrypted directory
            
        Returns:
            Tuple of (success_count, failure_count)
        """
        directory_path = Path(directory_path)
        if not directory_path.exists() or not directory_path.is_dir():
            self.logger.error(f"Directory not found: {directory_path}")
            return (0, 0)
        
        metadata_file = directory_path / ".encryption_metadata.json"
        if not metadata_file.exists():
            self.logger.error(f"Encryption metadata not found in {directory_path}")
            return (0, 0)
        
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        except Exception as e:
            self.logger.error(f"Error reading encryption metadata: {e}")
            return (0, 0)
        
        success_count = 0
        failure_count = 0
        
        # Decrypt files listed in the metadata
        for rel_path in metadata.get("encrypted_files", []):
            file_path = directory_path / rel_path
            if file_path.exists():
                if self.decrypt_file(file_path):
                    success_count += 1
                else:
                    failure_count += 1
        
        # Remove the metadata file
        metadata_file.unlink()
        
        self.logger.info(f"Decrypted {success_count} files in {directory_path} "
                        f"({failure_count} failures)")
        
        return (success_count, failure_count)
    
    def encrypt_metadata(self, metadata: Dict, key_id: str = None) -> Dict:
        """
        Encrypt sensitive metadata.
        
        Args:
            metadata: Dictionary containing metadata
            key_id: Key ID to use for encryption (uses active key if None)
            
        Returns:
            Dictionary with encrypted sensitive fields
        """
        try:
            # Get the encryption key
            if key_id is None:
                key_id, key_material = self.key_manager.get_active_key("encryption")
            else:
                key_material = self.key_manager.get_key(key_id)
            
            # Determine which fields to encrypt
            sensitive_fields = self.config.get("security", {}).get(
                "sensitive_metadata_fields", ["description", "user_data"]
            )
            
            # Create a copy of the metadata
            encrypted_metadata = metadata.copy()
            
            # Encrypt sensitive fields
            for field in sensitive_fields:
                if field in metadata and metadata[field]:
                    # Convert to JSON string
                    field_data = json.dumps(metadata[field]).encode()
                    
                    # Encrypt the field
                    algorithm = self.config['security']['encryption']['algorithm']
                    if algorithm == "aes-256-gcm":
                        cipher = AESGCM(key_material)
                        nonce = os.urandom(12)
                        ciphertext = cipher.encrypt(nonce, field_data, None)
                    elif algorithm == "chacha20-poly1305":
                        cipher = ChaCha20Poly1305(key_material)
                        nonce = os.urandom(12)
                        ciphertext = cipher.encrypt(nonce, field_data, None)
                    else:
                        continue
                    
                    # Replace with encrypted data
                    encrypted_metadata[field] = {
                        "encrypted": True,
                        "algorithm": algorithm,
                        "key_id": key_id,
                        "nonce": base64.b64encode(nonce).decode(),
                        "data": base64.b64encode(ciphertext).decode()
                    }
            
            # Add encryption metadata
            encrypted_metadata["_encrypted"] = True
            
            return encrypted_metadata
        except Exception as e:
            self.logger.error(f"Error encrypting metadata: {e}")
            return metadata
    
    def decrypt_metadata(self, metadata: Dict) -> Dict:
        """
        Decrypt encrypted metadata.
        
        Args:
            metadata: Dictionary containing encrypted metadata
            
        Returns:
            Dictionary with decrypted fields
        """
        try:
            if not metadata.get("_encrypted", False):
                return metadata
            
            # Create a copy of the metadata
            decrypted_metadata = metadata.copy()
            
            # Find and decrypt encrypted fields
            for field, value in metadata.items():
                if isinstance(value, dict) and value.get("encrypted", False):
                    # Get the encryption key
                    key_id = value["key_id"]
                    try:
                        key_material = self.key_manager.get_key(key_id)
                    except ValueError:
                        self.logger.error(f"Encryption key not found: {key_id}")
                        continue
                    
                    # Get the algorithm and nonce
                    algorithm = value["algorithm"]
                    nonce = base64.b64decode(value["nonce"])
                    
                    # Decode the ciphertext
                    ciphertext = base64.b64decode(value["data"])
                    
                    # Decrypt the data
                    if algorithm == "aes-256-gcm":
                        cipher = AESGCM(key_material)
                        plaintext = cipher.decrypt(nonce, ciphertext, None)
                    elif algorithm == "chacha20-poly1305":
                        cipher = ChaCha20Poly1305(key_material)
                        plaintext = cipher.decrypt(nonce, ciphertext, None)
                    else:
                        continue
                    
                    # Replace with decrypted data
                    decrypted_metadata[field] = json.loads(plaintext.decode())
            
            # Remove encryption flag
            if "_encrypted" in decrypted_metadata:
                del decrypted_metadata["_encrypted"]
            
            return decrypted_metadata
        except Exception as e:
            self.logger.error(f"Error decrypting metadata: {e}")
            return metadata
