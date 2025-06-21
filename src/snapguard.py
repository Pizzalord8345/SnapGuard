import json
import logging
import os
import subprocess
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import hashlib
import hmac
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

class SnapGuard:
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_audit_logging()
        self.bus = dbus.SystemBus()
        self.polkit = self.bus.get_object('org.freedesktop.PolicyKit1', '/org/freedesktop/PolicyKit1/Authority')
        self._setup_encryption()
        self._setup_signing()

    def _setup_encryption(self):
        if self.config['security']['encryption']['enabled']:
            key_file = Path(self.config['security']['encryption']['key_file'])
            salt_file = key_file.with_suffix('.salt')
            if not key_file.exists():
                self._generate_encryption_key()

            if salt_file.exists():
                with open(salt_file, 'rb') as sf:
                    salt = sf.read()
            else:
                salt = os.urandom(16)
                with open(salt_file, 'wb') as sf:
                    sf.write(salt)
                os.chmod(salt_file, 0o600)

            with open(key_file, 'rb') as f:
                key_data = f.read()
                # derive the key with PBKDF2
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                self.encryption_key = base64.urlsafe_b64encode(kdf.derive(key_data))

    def _setup_signing(self):
        if self.config['security']['signing']['enabled']:
            key_file = Path(self.config['security']['signing']['key_file'])
            if not key_file.exists():
                self._generate_signing_key()
            with open(key_file, 'rb') as f:
                self.signing_key = f.read()

    def _generate_encryption_key(self):
        key = Fernet.generate_key()
        key_file = Path(self.config['security']['encryption']['key_file'])
        key_file.parent.mkdir(parents=True, exist_ok=True)
        with open(key_file, 'wb') as f:
            f.write(key)
        os.chmod(key_file, 0o600)

    def _generate_signing_key(self):
        key = os.urandom(32)
        key_file = Path(self.config['security']['signing']['key_file'])
        key_file.parent.mkdir(parents=True, exist_ok=True)
        with open(key_file, 'wb') as f:
            f.write(key)
        os.chmod(key_file, 0o600)

    def _setup_audit_logging(self):
        audit_log = Path(self.config['security']['audit_log'])
        audit_log.parent.mkdir(parents=True, exist_ok=True)
        self.audit_logger = logging.getLogger('audit')
        handler = logging.FileHandler(audit_log)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.audit_logger.addHandler(handler)
        self.audit_logger.setLevel(logging.INFO)

    def _audit_log(self, action: str, success: bool, details: str = ""):
        self.audit_logger.info(f"Action: {action}, Success: {success}, Details: {details}")

    def _encrypt_snapshot(self, snapshot_path: str) -> bool:
        if not self.config['security']['encryption']['enabled']:
            return True

        try:
            f = Fernet(self.encryption_key)
            snapshot_dir = Path(snapshot_path)
            
            # encrypt all files in the snapshot
            for file_path in snapshot_dir.rglob('*'):
                if file_path.is_file():
                    try:
                        with open(file_path, 'rb') as file:
                            original_data = file.read()
                        encrypted_data = f.encrypt(original_data)
                        with open(file_path, 'wb') as file:
                            file.write(encrypted_data)
                    except Exception as e:
                        logging.error(f"Failed to encrypt file {file_path}: {e}")
                        return False
            
            # create a metadata file for the encryption
            metadata = {
                'algorithm': self.config['security']['encryption']['algorithm'],
                'timestamp': datetime.now().isoformat(),
                'version': '1.0'
            }
            with open(snapshot_dir / '.encryption_metadata.json', 'w') as f:
                json.dump(metadata, f)
            
            return True
        except Exception as e:
            logging.error(f"Encryption failed: {e}")
            return False

    def _decrypt_snapshot(self, snapshot_path: str) -> bool:
        if not self.config['security']['encryption']['enabled']:
            logging.info("Encryption is not enabled. No decryption needed.")
            return True

        if not hasattr(self, 'encryption_key'):
            logging.error("Encryption key not available. Decryption cannot proceed.")
            return False

        try:
            f = Fernet(self.encryption_key)
            snapshot_dir = Path(snapshot_path)

            logging.info(f"Starting decryption for snapshot: {snapshot_path}")

            for file_path in snapshot_dir.rglob('*'):
                if file_path.is_file() and file_path.name != '.encryption_metadata.json' and file_path.name != '.signature_metadata.json':
                    try:
                        with open(file_path, 'rb') as file:
                            encrypted_data = file.read()

                        # Skip empty files as they might not be valid Fernet tokens
                        if not encrypted_data:
                            logging.debug(f"Skipping empty file: {file_path}")
                            continue

                        decrypted_data = f.decrypt(encrypted_data)
                        with open(file_path, 'wb') as file:
                            file.write(decrypted_data)
                        logging.debug(f"Successfully decrypted file: {file_path}")
                    except FileNotFoundError:
                        logging.warning(f"File not found during decryption (possibly already processed or a symlink issue): {file_path}")
                        # Depending on strictness, could return False here
                        continue # Or simply log and continue with other files
                    except (Fernet.InvalidToken, TypeError) as token_error: # TypeError for non-bytes token
                        logging.error(f"Failed to decrypt file {file_path} due to invalid token or data: {token_error}")
                        return False # If any file fails, decryption is considered failed
                    except Exception as e:
                        logging.error(f"An unexpected error occurred while decrypting file {file_path}: {e}")
                        return False

            # Attempt to remove the encryption metadata file
            metadata_file = snapshot_dir / '.encryption_metadata.json'
            if metadata_file.exists():
                try:
                    metadata_file.unlink()
                    logging.info(f"Successfully removed encryption metadata file: {metadata_file}")
                except Exception as e:
                    logging.warning(f"Failed to remove encryption metadata file {metadata_file}: {e}")
            else:
                logging.info("No encryption metadata file found to remove.")

            logging.info(f"Decryption completed successfully for snapshot: {snapshot_path}")
            return True
        except Exception as e:
            logging.error(f"Decryption process failed for snapshot {snapshot_path}: {e}", exc_info=True)
            return False

    def _sign_snapshot(self, snapshot_path: str) -> bool:
        if not self.config['security']['signing']['enabled']:
            return True

        try:
            snapshot_dir = Path(snapshot_path)
            signatures = {}
            
            # create signatures for all files
            for file_path in snapshot_dir.rglob('*'):
                if file_path.is_file():
                    try:
                        with open(file_path, 'rb') as file:
                            content = file.read()
                        relative_path = str(file_path.relative_to(snapshot_dir))
                        signature = hmac.new(
                            self.signing_key,
                            content,
                            hashlib.sha256
                        ).hexdigest()
                        signatures[relative_path] = signature
                    except Exception as e:
                        logging.error(f"Failed to sign file {file_path}: {e}")
                        return False
            
            # save the signatures in a metadata file
            metadata = {
                'signatures': signatures,
                'timestamp': datetime.now().isoformat(),
                'version': '1.0'
            }
            with open(snapshot_dir / '.signature_metadata.json', 'w') as f:
                json.dump(metadata, f)
            
            return True
        except Exception as e:
            logging.error(f"Signing failed: {e}")
            return False

    def verify_snapshot(self, snapshot_path: str) -> bool:
        """Verifies the integrity of a snapshot."""
        if not self.config['security']['signing']['enabled']:
            return True

        try:
            snapshot_dir = Path(snapshot_path)
            signature_file = snapshot_dir / '.signature_metadata.json'
            
            if not signature_file.exists():
                logging.error("No signature metadata found")
                return False
            
            with open(signature_file, 'r') as f:
                metadata = json.load(f)
            
            for relative_path, expected_signature in metadata['signatures'].items():
                file_path = snapshot_dir / relative_path
                if not file_path.exists():
                    logging.error(f"File not found: {relative_path}")
                    return False
                
                with open(file_path, 'rb') as file:
                    content = file.read()
                actual_signature = hmac.new(
                    self.signing_key,
                    content,
                    hashlib.sha256
                ).hexdigest()
                
                if actual_signature != expected_signature:
                    logging.error(f"Signature mismatch for file: {relative_path}")
                    return False
            
            return True
        except Exception as e:
            logging.error(f"Verification failed: {e}")
            return False

    def _load_config(self, config_path: str) -> Dict:
        with open(config_path, 'r') as f:
            return json.load(f)

    def _setup_logging(self):
        if self.config['logging']['enabled']:
            if self.config['logging']['journald']:
                logging.basicConfig(level=getattr(logging, self.config['logging']['level']))
            else:
                logging.basicConfig(
                    filename='snapguard.log',
                    level=getattr(logging, self.config['logging']['level']),
                    format='%(asctime)s - %(levelname)s - %(message)s'
                )

    def _check_polkit_auth(self, action_id: str) -> bool:
        try:
            subject = ('system-bus-name', {'name': dbus.String('org.snapguard')})
            result = self.polkit.CheckAuthorization(
                subject,
                action_id,
                {},
                dbus.UInt32(1),
                '',
                dbus_interface='org.freedesktop.PolicyKit1.Authority'
            )
            return result[0]
        except dbus.exceptions.DBusException as e:
            logging.error(f"Polkit authorization failed: {e}")
            return False

    def _generate_snapshot_name(self, subvolume_name: str, timestamp: str, description: Optional[str]) -> str:
        snapshot_name = f"snapshot_{subvolume_name}_{timestamp}"
        if description:
            snapshot_name += f"_{description}"
        return snapshot_name

    def _execute_btrfs_snapshot_command(self, subvolume_path: str, snapshot_target_path: str) -> bool:
        cmd = ['btrfs', 'subvolume', 'snapshot', subvolume_path, snapshot_target_path]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logging.info(f"Btrfs snapshot command successful: {' '.join(cmd)}")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to execute btrfs snapshot command: {' '.join(cmd)}. Error: {e.stderr}")
            return False

    def create_snapshot(self, description: Optional[str] = None) -> bool:
        if not self._check_polkit_auth('org.snapguard.create-snapshot'):
            self._audit_log("create_snapshot_auth_failed", False, "Polkit authorization failed")
            return False

        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            overall_success = True

            for subvol_config in self.config['snapshot']['subvolumes']:
                if not subvol_config['enabled']:
                    logging.info(f"Skipping disabled subvolume: {subvol_config['name']}")
                    continue

                snapshot_name = self._generate_snapshot_name(subvol_config['name'], timestamp, description)
                snapshot_target_path = f"{self.config['snapshot']['default_location']}/{snapshot_name}"

                logging.info(f"Attempting to create snapshot for subvolume: {subvol_config['name']} at {snapshot_target_path}")

                if self._execute_btrfs_snapshot_command(subvol_config['path'], snapshot_target_path):
                    snapshot_created_successfully = True
                    if self.config['security']['encryption']['enabled']:
                        logging.info(f"Encrypting snapshot: {snapshot_name}")
                        if not self._encrypt_snapshot(snapshot_target_path):
                            logging.error(f"Failed to encrypt snapshot: {snapshot_name}")
                            snapshot_created_successfully = False
                            # Decide if we should delete the partially failed snapshot
                            # For now, we'll leave it and mark overall_success as False

                    if snapshot_created_successfully and self.config['security']['signing']['enabled']:
                        logging.info(f"Signing snapshot: {snapshot_name}")
                        if not self._sign_snapshot(snapshot_target_path):
                            logging.error(f"Failed to sign snapshot: {snapshot_name}")
                            snapshot_created_successfully = False
                            # Decide if we should delete the partially failed snapshot

                    if snapshot_created_successfully:
                        logging.info(f"Snapshot created and processed successfully: {snapshot_name}")
                    else:
                        overall_success = False # Mark overall success as false if any step failed
                        # Consider what to do with a snapshot that was created but failed encryption/signing
                        # For now, it remains, but it's logged as an error.
                else:
                    # btrfs command itself failed
                    logging.error(f"Snapshot creation failed for subvolume: {subvol_config['name']}")
                    overall_success = False

            if overall_success:
                self._send_notification("Snapshot created", "All snapshots were created successfully.")
                self._audit_log("create_snapshot", True, f"Description: {description}. All subvolumes processed successfully.")
            else:
                self._send_notification("Snapshot failed", "One or more snapshots failed to create or process correctly. Check logs.")
                self._audit_log("create_snapshot", False, f"Description: {description}. Some subvolumes failed.")

            return overall_success
        except Exception as e:
            logging.error(f"An unexpected error occurred during create_snapshot: {e}", exc_info=True)
            self._audit_log("create_snapshot_exception", False, str(e))
            return False

    def decrypt_snapshot_for_restore(self, snapshot_path: str) -> bool:
        """
        Verifies and then decrypts a snapshot in place, preparing it for restoration.
        """
        logging.info(f"Attempting to decrypt snapshot for restore: {snapshot_path}")

        if not Path(snapshot_path).exists():
            logging.error(f"Snapshot path does not exist: {snapshot_path}")
            self._audit_log("decrypt_snapshot_for_restore", False, f"Snapshot not found: {snapshot_path}")
            return False

        if self.config['security']['signing']['enabled']:
            logging.info(f"Verifying snapshot integrity before decryption: {snapshot_path}")
            if not self.verify_snapshot(snapshot_path):
                logging.error(f"Snapshot verification failed for: {snapshot_path}. Decryption aborted.")
                self._audit_log("decrypt_snapshot_for_restore", False, f"Verification failed: {snapshot_path}")
                return False
            logging.info(f"Snapshot verification successful: {snapshot_path}")
        else:
            logging.warning("Signing is not enabled. Skipping snapshot verification before decryption.")

        if not self.config['security']['encryption']['enabled']:
            logging.info("Encryption is not enabled. No decryption needed for restore.")
            self._audit_log("decrypt_snapshot_for_restore", True, f"No decryption needed (encryption disabled): {snapshot_path}")
            return True

        decrypt_success = self._decrypt_snapshot(snapshot_path)

        if decrypt_success:
            logging.info(f"Snapshot decrypted successfully for restore: {snapshot_path}")
            self._audit_log("decrypt_snapshot_for_restore", True, f"Successfully decrypted: {snapshot_path}")
        else:
            logging.error(f"Snapshot decryption failed for restore: {snapshot_path}")
            self._audit_log("decrypt_snapshot_for_restore", False, f"Decryption failed: {snapshot_path}")

        return decrypt_success

    def list_snapshots(self) -> List[Dict]:
        try:
            snapshots = []
            snapshot_dir = Path(self.config['snapshot']['default_location'])
            for snapshot in snapshot_dir.iterdir():
                if snapshot.is_dir():
                    snapshots.append({
                        'name': snapshot.name,
                        'path': str(snapshot),
                        'created': datetime.fromtimestamp(snapshot.stat().st_ctime)
                    })
            return sorted(snapshots, key=lambda x: x['created'], reverse=True)
        except Exception as e:
            logging.error(f"Error listing snapshots: {e}")
            return []

    def delete_snapshot(self, snapshot_name: str) -> bool:
        if not self._check_polkit_auth('org.snapguard.delete-snapshot'):
            return False

        try:
            snapshot_path = Path(self.config['snapshot']['default_location']) / snapshot_name
            cmd = ['btrfs', 'subvolume', 'delete', str(snapshot_path)]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logging.info(f"Snapshot deleted successfully: {snapshot_name}")
                self._send_notification("Snapshot deleted", f"Snapshot {snapshot_name} was deleted successfully")
                return True
            else:
                logging.error(f"Failed to delete snapshot: {result.stderr}")
                return False
        except Exception as e:
            logging.error(f"Error deleting snapshot: {e}")
            return False

    def _send_notification(self, title: str, message: str):
        """Sends notifications through various channels."""
        if self.config['notifications']['enabled']:
            # Desktop notification
            try:
                subprocess.run(['notify-send', title, message])
            except Exception as e:
                logging.error(f"Failed to send desktop notification: {e}")
            
            # Email notification
            if self.config['notifications'].get('email', {}).get('enabled', False):
                self._send_email_notification(title, message)

    def _send_email_notification(self, title: str, message: str):
        """Sends an email notification."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            email_config = self.config['notifications']['email']
            
            msg = MIMEMultipart()
            msg['From'] = email_config['from']
            msg['To'] = email_config['to']
            msg['Subject'] = f"SnapGuard: {title}"
            
            body = f"""
            {message}
            
            Timestamp: {datetime.now().isoformat()}
            System: {os.uname().nodename}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                if email_config.get('use_tls', True):
                    server.starttls()
                if email_config.get('username'):
                    server.login(email_config['username'], email_config['password'])
                server.send_message(msg)
                
            logging.info("Email notification sent successfully")
        except Exception as e:
            logging.error(f"Failed to send email notification: {e}")

    def update_schedule(self, schedule_type: str, time: str) -> bool:
        try:
            self.config['snapshot']['schedule']['type'] = schedule_type
            self.config['snapshot']['schedule']['time'] = time
            
            # Update systemd timer
            timer_content = f"""OnCalendar=*-*-* {time}
Persistent=true"""
            
            with open('/etc/systemd/system/snapguard.timer', 'w') as f:
                f.write(timer_content)
            
            subprocess.run(['systemctl', 'daemon-reload'])
            subprocess.run(['systemctl', 'restart', 'snapguard.timer'])
            
            return True
        except Exception as e:
            logging.error(f"Error updating schedule: {e}")
            return False

    def cleanup_old_snapshots(self) -> bool:
        """Cleans up old snapshots based on retention policies."""
        try:
            retention = self.config['snapshot']['retention']
            now = datetime.now()
            snapshots = self.list_snapshots()
            
            # Group snapshots by type (daily, weekly, monthly)
            daily_snapshots = []
            weekly_snapshots = []
            monthly_snapshots = []
            
            for snapshot in snapshots:
                age = now - snapshot['created']
                if age.days <= 7:  # Last 7 days
                    daily_snapshots.append(snapshot)
                elif age.days <= 30:  # Last month
                    weekly_snapshots.append(snapshot)
                else:  # Older than a month
                    monthly_snapshots.append(snapshot)
            
            # Keep the newest snapshots according to retention policies
            snapshots_to_keep = set()
            
            # Daily snapshots
            daily_snapshots.sort(key=lambda x: x['created'], reverse=True)
            snapshots_to_keep.update(s['name'] for s in daily_snapshots[:retention['daily']])
            
            # Weekly snapshots (one per week)
            weekly_snapshots.sort(key=lambda x: x['created'], reverse=True)
            weekly_groups = {}
            for snapshot in weekly_snapshots:
                week = snapshot['created'].isocalendar()[1]
                if week not in weekly_groups:
                    weekly_groups[week] = snapshot
            snapshots_to_keep.update(s['name'] for s in list(weekly_groups.values())[:retention['weekly']])
            
            # Monthly snapshots (one per month)
            monthly_snapshots.sort(key=lambda x: x['created'], reverse=True)
            monthly_groups = {}
            for snapshot in monthly_snapshots:
                month = snapshot['created'].strftime('%Y-%m')
                if month not in monthly_groups:
                    monthly_groups[month] = snapshot
            snapshots_to_keep.update(s['name'] for s in list(monthly_groups.values())[:retention['monthly']])
            
            # Delete all snapshots that should not be kept
            success = True
            for snapshot in snapshots:
                if snapshot['name'] not in snapshots_to_keep:
                    if not self.delete_snapshot(snapshot['name']):
                        logging.error(f"Failed to delete old snapshot: {snapshot['name']}")
                        success = False
            
            if success:
                self._send_notification("Cleanup", "Old snapshots have been cleaned up")
                self._audit_log("cleanup_snapshots", True, 
                              f"Kept: {len(snapshots_to_keep)}, Deleted: {len(snapshots) - len(snapshots_to_keep)}")
            else:
                self._send_notification("Cleanup Failed", "Some old snapshots could not be deleted")
                self._audit_log("cleanup_snapshots", False, "Partial cleanup completed")
            
            return success
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")
            self._audit_log("cleanup_snapshots", False, str(e))
            return False

    def export_backup(self, destination: str) -> bool:
        if not self.config['backup']['enabled']:
            return False

        try:
            destination_path = Path(destination)
            destination_path.mkdir(parents=True, exist_ok=True)
            
            # Create Backup-Metadata
            backup_metadata = {
                'timestamp': datetime.now().isoformat(),
                'snapshots': [],
                'version': '1.0'
            }
            
            for snapshot in self.list_snapshots():
                source_path = Path(snapshot['path'])
                dest_path = destination_path / snapshot['name']
                
                # Verify the Integrity of all Snapshots
                if not self.verify_snapshot(str(source_path)):
                    logging.error(f"Snapshot verification failed: {snapshot['name']}")
                    continue
                
                # Copy all Snapshots
                shutil.copytree(source_path, dest_path, symlinks=True)
                
                # Copy Metadata-filetypes
                for meta_file in ['.encryption_metadata.json', '.signature_metadata.json']:
                    meta_path = source_path / meta_file
                    if meta_path.exists():
                        shutil.copy2(meta_path, dest_path / meta_file)
                
                # add Snapshot Information to the Metadata
                backup_metadata['snapshots'].append({
                    'name': snapshot['name'],
                    'created': snapshot['created'].isoformat(),
                    'path': str(dest_path.relative_to(destination_path))
                })
            
            # Save Backup-Metadata
            with open(destination_path / 'backup_metadata.json', 'w') as f:
                json.dump(backup_metadata, f, indent=2)
            
            # Create a checksum for the whole backup
            backup_hash = self._calculate_backup_hash(destination_path)
            with open(destination_path / 'backup_hash.sha256', 'w') as f:
                f.write(backup_hash)
            
            self._send_notification("Backup", "Backup export completed successfully")
            self._audit_log("export_backup", True, 
                          f"Destination: {destination}, Snapshots: {len(backup_metadata['snapshots'])}")
            return True
        except Exception as e:
            logging.error(f"Error during backup export: {e}")
            self._audit_log("export_backup", False, str(e))
            return False

    def _calculate_backup_hash(self, backup_path: Path) -> str:
        """Berechnet eine Prüfsumme für das gesamte Backup."""
        hash_object = hashlib.sha256()
        
        # Sort Files for consistent Hash-Calculation
        files = sorted(backup_path.rglob('*'))
        for file_path in files:
            if file_path.is_file():
                relative_path = str(file_path.relative_to(backup_path))
                hash_object.update(relative_path.encode())
                with open(file_path, 'rb') as f:
                    while chunk := f.read(8192):
                        hash_object.update(chunk)
        
        return hash_object.hexdigest() 
