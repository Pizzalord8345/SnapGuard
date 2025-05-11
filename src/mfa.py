#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
import base64
import time
import hmac
import hashlib
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta

class MFAManager:
    """
    Multi-factor authentication manager for SnapGuard.
    Supports TOTP and FIDO2/U2F authentication methods.
    """
    
    def __init__(self, config_path: str = "config.json"):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        self._initialize_mfa_storage()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file."""
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def _initialize_mfa_storage(self) -> None:
        """Initialize MFA storage directory."""
        mfa_dir = Path(self.config['security']['mfa_directory'])
        mfa_dir.mkdir(parents=True, exist_ok=True)
    
    def setup_totp(self, user_id: str, issuer: str = "SnapGuard") -> Dict:
        """
        Set up Time-based One-Time Password (TOTP) for a user.
        
        Args:
            user_id: User identifier
            issuer: Name of the issuing application
            
        Returns:
            Dictionary with TOTP setup information
        """
        try:
            # Import pyotp only when needed
            import pyotp
        except ImportError:
            self.logger.error("pyotp package not installed. Install with: pip install pyotp")
            return {"error": "TOTP support not available"}
        
        # Generate a random secret
        secret = pyotp.random_base32()
        
        # Create a TOTP object
        totp = pyotp.TOTP(secret)
        
        # Generate the provisioning URI for QR code
        uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_id,
            issuer_name=issuer
        )
        
        # Save the TOTP configuration
        mfa_dir = Path(self.config['security']['mfa_directory'])
        user_file = mfa_dir / f"{user_id}_totp.json"
        
        mfa_data = {
            "user_id": user_id,
            "type": "totp",
            "secret": secret,
            "created": datetime.now().isoformat(),
            "last_used": None,
            "enabled": True
        }
        
        with open(user_file, 'w') as f:
            json.dump(mfa_data, f, indent=2)
        
        self.logger.info(f"TOTP setup for user: {user_id}")
        
        return {
            "user_id": user_id,
            "secret": secret,
            "uri": uri,
            "status": "setup_complete"
        }
    
    def verify_totp(self, user_id: str, code: str) -> bool:
        """
        Verify a TOTP code.
        
        Args:
            user_id: User identifier
            code: TOTP code to verify
            
        Returns:
            True if verification succeeds, False otherwise
        """
        try:
            import pyotp
        except ImportError:
            self.logger.error("pyotp package not installed")
            return False
        
        mfa_dir = Path(self.config['security']['mfa_directory'])
        user_file = mfa_dir / f"{user_id}_totp.json"
        
        if not user_file.exists():
            self.logger.error(f"TOTP data not found for user: {user_id}")
            return False
        
        try:
            with open(user_file, 'r') as f:
                mfa_data = json.load(f)
            
            if not mfa_data.get("enabled", False):
                self.logger.error(f"TOTP disabled for user: {user_id}")
                return False
            
            secret = mfa_data["secret"]
            totp = pyotp.TOTP(secret)
            
            # Verify the code
            if totp.verify(code):
                # Update last used timestamp
                mfa_data["last_used"] = datetime.now().isoformat()
                with open(user_file, 'w') as f:
                    json.dump(mfa_data, f, indent=2)
                
                self.logger.info(f"TOTP verification successful for user: {user_id}")
                return True
            else:
                self.logger.warning(f"TOTP verification failed for user: {user_id}")
                return False
        except Exception as e:
            self.logger.error(f"Error verifying TOTP: {e}")
            return False
    
    def setup_fido2(self, user_id: str) -> Dict:
        """
        Set up FIDO2/U2F authentication for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with FIDO2 registration options
        """
        try:
            # Import fido2 only when needed
            from fido2.server import Fido2Server
            from fido2.webauthn import PublicKeyCredentialRpEntity
        except ImportError:
            self.logger.error("fido2 package not installed. Install with: pip install fido2")
            return {"error": "FIDO2 support not available"}
        
        # This is a simplified implementation - in a real application,
        # you would need to handle the complete FIDO2 registration flow
        
        # Create a new directory for MFA data if it doesn't exist
        mfa_dir = Path(self.config['security']['mfa_directory'])
        
        # Generate a random challenge
        challenge = os.urandom(32)
        
        # In a real implementation, you would:
        # 1. Create a FIDO2 server
        # 2. Generate registration options
        # 3. Send these to the client
        # 4. Process the registration response
        
        # For now, we'll just save the challenge as a placeholder
        mfa_data = {
            "user_id": user_id,
            "type": "fido2",
            "created": datetime.now().isoformat(),
            "challenge": base64.b64encode(challenge).decode(),
            "registered": False,
            "enabled": False
        }
        
        with open(mfa_dir / f"{user_id}_fido2.json", 'w') as f:
            json.dump(mfa_data, f, indent=2)
        
        self.logger.info(f"FIDO2 setup initiated for user: {user_id}")
        
        return {
            "user_id": user_id,
            "challenge": base64.b64encode(challenge).decode(),
            "status": "pending_registration"
        }
    
    def complete_fido2_registration(self, user_id: str, credential_data: Dict) -> bool:
        """
        Complete FIDO2 registration process.
        
        Args:
            user_id: User identifier
            credential_data: Credential data from the authenticator
            
        Returns:
            True if registration succeeds, False otherwise
        """
        # This is a simplified implementation - in a real application,
        # you would need to validate the credential data properly
        
        mfa_dir = Path(self.config['security']['mfa_directory'])
        user_file = mfa_dir / f"{user_id}_fido2.json"
        
        if not user_file.exists():
            self.logger.error(f"FIDO2 setup data not found for user: {user_id}")
            return False
        
        try:
            with open(user_file, 'r') as f:
                mfa_data = json.load(f)
            
            # In a real implementation, you would:
            # 1. Verify the attestation
            # 2. Store the credential public key
            # 3. Store the credential ID
            
            # For now, we'll just store the credential data as-is
            mfa_data["credential"] = credential_data
            mfa_data["registered"] = True
            mfa_data["enabled"] = True
            mfa_data["registration_completed"] = datetime.now().isoformat()
            
            with open(user_file, 'w') as f:
                json.dump(mfa_data, f, indent=2)
            
            self.logger.info(f"FIDO2 registration completed for user: {user_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error completing FIDO2 registration: {e}")
            return False
    
    def verify_fido2(self, user_id: str, assertion_data: Dict) -> bool:
        """
        Verify a FIDO2 assertion.
        
        Args:
            user_id: User identifier
            assertion_data: Assertion data from the authenticator
            
        Returns:
            True if verification succeeds, False otherwise
        """
        # This is a simplified implementation - in a real application,
        # you would need to validate the assertion properly
        
        mfa_dir = Path(self.config['security']['mfa_directory'])
        user_file = mfa_dir / f"{user_id}_fido2.json"
        
        if not user_file.exists():
            self.logger.error(f"FIDO2 data not found for user: {user_id}")
            return False
        
        try:
            with open(user_file, 'r') as f:
                mfa_data = json.load(f)
            
            if not mfa_data.get("registered", False) or not mfa_data.get("enabled", False):
                self.logger.error(f"FIDO2 not registered or disabled for user: {user_id}")
                return False
            
            # In a real implementation, you would:
            # 1. Generate assertion options
            # 2. Verify the assertion using the stored credential
            
            # For now, we'll just log the attempt and return True as a placeholder
            mfa_data["last_used"] = datetime.now().isoformat()
            
            with open(user_file, 'w') as f:
                json.dump(mfa_data, f, indent=2)
            
            self.logger.info(f"FIDO2 verification for user: {user_id} (placeholder implementation)")
            return True
        except Exception as e:
            self.logger.error(f"Error verifying FIDO2 assertion: {e}")
            return False
    
    def require_mfa_for_operation(self, operation: str) -> bool:
        """
        Check if an operation requires MFA.
        
        Args:
            operation: Operation name
            
        Returns:
            True if MFA is required, False otherwise
        """
        mfa_policy = self.config.get("security", {}).get("mfa_policy", {})
        required_operations = mfa_policy.get("required_operations", [])
        
        return operation in required_operations
    
    def get_available_methods(self, user_id: str) -> List[str]:
        """
        Get available MFA methods for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of available MFA methods
        """
        methods = []
        mfa_dir = Path(self.config['security']['mfa_directory'])
        
        # Check for TOTP
        totp_file = mfa_dir / f"{user_id}_totp.json"
        if totp_file.exists():
            try:
                with open(totp_file, 'r') as f:
                    totp_data = json.load(f)
                if totp_data.get("enabled", False):
                    methods.append("totp")
            except Exception:
                pass
        
        # Check for FIDO2
        fido2_file = mfa_dir / f"{user_id}_fido2.json"
        if fido2_file.exists():
            try:
                with open(fido2_file, 'r') as f:
                    fido2_data = json.load(f)
                if fido2_data.get("enabled", False) and fido2_data.get("registered", False):
                    methods.append("fido2")
            except Exception:
                pass
        
        return methods
    
    def disable_method(self, user_id: str, method: str) -> bool:
        """
        Disable an MFA method for a user.
        
        Args:
            user_id: User identifier
            method: MFA method to disable
            
        Returns:
            True if successful, False otherwise
        """
        mfa_dir = Path(self.config['security']['mfa_directory'])
        
        if method == "totp":
            file_path = mfa_dir / f"{user_id}_totp.json"
        elif method == "fido2":
            file_path = mfa_dir / f"{user_id}_fido2.json"
        else:
            self.logger.error(f"Unknown MFA method: {method}")
            return False
        
        if not file_path.exists():
            self.logger.error(f"MFA data not found for user: {user_id}, method: {method}")
            return False
        
        try:
            with open(file_path, 'r') as f:
                mfa_data = json.load(f)
            
            mfa_data["enabled"] = False
            mfa_data["disabled_at"] = datetime.now().isoformat()
            
            with open(file_path, 'w') as f:
                json.dump(mfa_data, f, indent=2)
            
            self.logger.info(f"Disabled {method} for user: {user_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error disabling {method}: {e}")
            return False
    
    def generate_backup_codes(self, user_id: str, count: int = 10) -> List[str]:
        """
        Generate backup codes for a user.
        
        Args:
            user_id: User identifier
            count: Number of backup codes to generate
            
        Returns:
            List of generated backup codes
        """
        mfa_dir = Path(self.config['security']['mfa_directory'])
        backup_file = mfa_dir / f"{user_id}_backup_codes.json"
        
        # Generate random codes
        codes = []
        for _ in range(count):
            # Generate a 10-character code
            code = base64.b32encode(os.urandom(5)).decode().replace('=', '').lower()
            codes.append(code)
        
        # Hash the codes for storage
        hashed_codes = []
        for code in codes:
            code_hash = hashlib.sha256(code.encode()).hexdigest()
            hashed_codes.append({
                "hash": code_hash,
                "used": False
            })
        
        # Save the hashed codes
        backup_data = {
            "user_id": user_id,
            "created": datetime.now().isoformat(),
            "codes": hashed_codes
        }
        
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        self.logger.info(f"Generated {count} backup codes for user: {user_id}")
        
        return codes
    
    def verify_backup_code(self, user_id: str, code: str) -> bool:
        """
        Verify a backup code.
        
        Args:
            user_id: User identifier
            code: Backup code to verify
            
        Returns:
            True if verification succeeds, False otherwise
        """
        mfa_dir = Path(self.config['security']['mfa_directory'])
        backup_file = mfa_dir / f"{user_id}_backup_codes.json"
        
        if not backup_file.exists():
            self.logger.error(f"Backup codes not found for user: {user_id}")
            return False
        
        try:
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            # Hash the provided code
            code_hash = hashlib.sha256(code.encode()).hexdigest()
            
            # Check if the code exists and hasn't been used
            for i, stored_code in enumerate(backup_data["codes"]):
                if stored_code["hash"] == code_hash and not stored_code["used"]:
                    # Mark the code as used
                    backup_data["codes"][i]["used"] = True
                    backup_data["codes"][i]["used_at"] = datetime.now().isoformat()
                    
                    with open(backup_file, 'w') as f:
                        json.dump(backup_data, f, indent=2)
                    
                    self.logger.info(f"Backup code verification successful for user: {user_id}")
                    return True
            
            self.logger.warning(f"Backup code verification failed for user: {user_id}")
            return False
        except Exception as e:
            self.logger.error(f"Error verifying backup code: {e}")
            return False