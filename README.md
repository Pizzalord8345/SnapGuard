# SnapGuard

An advanced snapshot manager for Linux systems with Btrfs support.

## Main Features

### Security
- **File-level encryption**: Each file is individually encrypted with AES-256-GCM
- **Secure key management**: 
  - Key derivation with PBKDF2 (100,000 iterations)
  - Separate keys for encryption and signing
  - Secure key storage in protected directories
- **Digital signing**: 
  - HMAC-SHA256 signatures for each file
  - Integrity verification before export
  - Snapshot verification during restoration

### Snapshot Management
- **Intelligent retention**:
  - Differentiated retention policies (daily, weekly, monthly)
  - Automatic selection of important snapshots
  - Configurable retention periods
- **Multiple subvolumes**: 
  - Support for multiple Btrfs subvolumes
  - Individual configuration per subvolume
  - Parallel snapshot creation

### Backup and Export
- **Secure backups**:
  - Overall backup checksum (SHA-256)
  - Integrity verification before export
  - Complete metadata documentation
- **Flexible export options**:
  - Support for various target media
  - Preservation of all security features
  - Automatic verification after export

### User Interface
- **GTK-based GUI**:
  - Clear overview of all snapshots
  - Easy management of retention policies
  - Security settings configuration
- **Systemd integration**:
  - Automatic snapshot creation
  - Configurable schedules
  - Reliable operation as system service

### Monitoring and Logging
- **Detailed audit logging**:
  - Logging of all operations
  - Success and error logs
  - Metrics and statistics
- **Notifications**:
  - Desktop notifications
  - Email notifications (optional)
  - System logging

## Installation

See [INSTALL.md](INSTALL.md) for detailed installation instructions.

## Configuration

Configuration is done via `config.json`. Important settings:

```json
{
    "snapshot": {
        "subvolumes": [
            {
                "path": "/",
                "name": "root",
                "enabled": true
            }
        ],
        "retention": {
            "daily": 7,
            "weekly": 4,
            "monthly": 12
        }
    },
    "security": {
        "encryption": {
            "enabled": true,
            "algorithm": "aes-256-gcm"
        },
        "signing": {
            "enabled": true
        }
    }
}
```

## Security Features

### Encryption
- AES-256-GCM for maximum security
- Individual file encryption
- Encryption metadata
- Secure key derivation with PBKDF2

### Integrity
- HMAC-SHA256 signatures
- Verification before export
- Overall backup checksum
- Automatic integrity verification

### Access Control
- Polkit integration
- No direct root access
- Secure permission management
- Audit logging of all operations

## Development

### Dependencies
- Python 3.6+
- GTK 3.0
- Btrfs
- Systemd
- Polkit

### Development Environment
```bash
git clone https://github.com/yourusername/snapguard.git
cd snapguard
pip install -r requirements.txt
```

## License

Apache 2.0 License

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on the contribution process.
