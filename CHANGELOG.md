# Changelog

All notable changes to SnapGuard will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-05-15

### Added
- **Enhanced Security**
  - Key rotation mechanism for encryption and signing keys
  - Support for hardware security modules (HSM/TPM)
  - Integration with system keyring services (GNOME Keyring, KWallet)
  - ChaCha20-Poly1305 encryption algorithm support
  - Per-file selective encryption for sensitive files
  - Encrypted snapshot names and metadata
  - Multi-factor authentication for critical operations
  - FIDO2/U2F security key support

- **Performance Optimizations**
  - Multi-threaded encryption/decryption for faster operations
  - Incremental snapshot support
  - Optimized snapshot verification with directory checksums
  - I/O throttling to limit system impact
  - Compression options for snapshots
  - Smart scheduling for system idle time

- **Recovery Improvements**
  - Bootable recovery environment creation
  - File-level restoration capabilities
  - "Time machine" style browser for snapshot contents

- **Monitoring and Reporting**
  - Dashboard with snapshot statistics and storage trends
  - Health checks for snapshot integrity
  - Scheduled email reports on backup status

- **Collaboration Features**
  - Multi-user support with permission levels
  - Shared snapshots for team environments
  - Comments and tagging for snapshots

- **Storage Efficiency**
  - Content-aware deduplication
  - Block-level deduplication for efficient storage

- **User Interface**
  - Dark mode support
  - Modern responsive UI
  - Visualization tools for snapshot relationships

- **Integration**
  - Plugin system for extending functionality
  - Support for exporting to/importing from other backup formats
  - Hooks for popular backup solutions

### Changed
- Completely redesigned user interface
- Improved configuration system with more options
- Enhanced logging and audit trail
- Updated documentation with comprehensive guides

### Fixed
- Multiple security vulnerabilities in encryption implementation
- Performance bottlenecks in snapshot creation
- UI responsiveness issues
- Memory leaks during large snapshot operations

## [1.2.0] - 2024-12-10

### Added
- Support for OverlayFS snapshots
- Basic snapshot search functionality
- Improved error reporting

### Changed
- Updated dependencies to latest versions
- Improved snapshot listing performance

### Fixed
- Issue with snapshot deletion on certain filesystems
- UI freezes when handling large snapshots
- Configuration file parsing errors

## [1.1.0] - 2024-08-22

### Added
- Email notifications for snapshot events
- Basic scheduling capabilities
- Command-line interface improvements

### Changed
- Enhanced snapshot metadata format
- Improved error handling

### Fixed
- Permission issues when running as non-root
- Configuration file not being created properly
- UI display issues on high-DPI screens

## [1.0.0] - 2024-05-01

### Added
- Initial release
- Basic snapshot creation and management
- Simple BtrFS integration
- GTK-based user interface
- Configuration system
- Basic encryption support