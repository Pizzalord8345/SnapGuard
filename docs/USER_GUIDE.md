# SnapGuard User Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Getting Started](#getting-started)
4. [Basic Usage](#basic-usage)
5. [Advanced Features](#advanced-features)
   - [Enhanced Security](#enhanced-security)
   - [Performance Optimizations](#performance-optimizations)
   - [Storage Efficiency](#storage-efficiency)
   - [Recovery Options](#recovery-options)
   - [User Interface](#user-interface)
6. [Configuration](#configuration)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)

## Introduction

SnapGuard is a modern, secure, and user-friendly snapshot & backup manager for Linux using BtrFS and OverlayFS. It provides a permissive alternative to Snapper with enhanced security features, performance optimizations, and a user-friendly GUI interface.

### Key Features

- **Enhanced Security**: AES-256-GCM encryption, key rotation, and multi-factor authentication
- **Performance Optimizations**: Parallel processing, I/O throttling, and smart scheduling
- **Storage Efficiency**: File and block-level deduplication, compression
- **Advanced Recovery**: File-level restoration, bootable recovery environment, time machine browser
- **User-Friendly Interface**: Modern GTK-based GUI with dark mode support and dashboard

## Installation

Please refer to the [INSTALL.md](../INSTALL.md) file for detailed installation instructions.

## Getting Started

### First Launch

When you first launch SnapGuard, you'll be presented with the main window showing the Dashboard. From here, you can:

1. View snapshot statistics and system health
2. Create and manage snapshots
3. Configure settings
4. Access advanced features

### Initial Configuration

Before creating your first snapshot, you should configure SnapGuard according to your needs:

1. Go to the Settings panel by clicking on the gear icon in the header bar
2. Configure general settings:
   - Snapshot location
   - Retention policy
   - Automatic snapshot schedule
3. Configure security settings:
   - Encryption options
   - Key rotation policy
   - Multi-factor authentication
4. Configure performance settings:
   - Parallel processing
   - I/O throttling
   - Smart scheduling
5. Configure storage settings:
   - Deduplication
   - Compression
6. Click "Save Settings" to apply your configuration

## Basic Usage

### Creating a Snapshot

To create a snapshot:

1. Click the "Create Snapshot" button in the Snapshots panel
2. Enter a description for the snapshot (optional)
3. Choose whether to encrypt and deduplicate the snapshot
4. Click "OK" to create the snapshot

### Viewing Snapshots

The Snapshots panel shows a list of all your snapshots. For each snapshot, you can see:

- Name
- Creation date and time
- Description
- Size
- Type (BtrFS or OverlayFS)

### Restoring a Snapshot

To restore a complete snapshot:

1. Select the snapshot in the Snapshots panel
2. Click the "Restore" button
3. Confirm the restoration
4. Wait for the restoration to complete

### Deleting a Snapshot

To delete a snapshot:

1. Select the snapshot in the Snapshots panel
2. Click the "Delete" button
3. Confirm the deletion

## Advanced Features

### Enhanced Security

#### Encryption

SnapGuard supports strong encryption for your snapshots:

1. Go to Settings > Security
2. Enable encryption
3. Choose an encryption algorithm (AES-256-GCM or ChaCha20-Poly1305)
4. Optionally enable selective encryption to encrypt only sensitive files

#### Key Rotation

Regular key rotation enhances security:

1. Go to Settings > Security > Key Rotation
2. Enable automatic key rotation
3. Set the maximum key age (default: 90 days)
4. Click "Rotate Keys Now" to manually rotate keys

#### Multi-Factor Authentication

Add an extra layer of security with MFA:

1. Go to Settings > Security > Multi-Factor Authentication
2. Enable MFA
3. Click "Setup MFA"
4. Choose an MFA method (TOTP or FIDO2/U2F)
5. Follow the setup instructions
6. Select which operations require MFA

### Performance Optimizations

#### Parallel Processing

Speed up snapshot operations with parallel processing:

1. Go to Settings > Performance
2. Enable parallel processing
3. Set the maximum number of worker threads
4. Optionally enable process-based parallelism for CPU-bound tasks

#### I/O Throttling

Limit system impact during snapshot operations:

1. Go to Settings > Performance > I/O Throttling
2. Enable I/O throttling
3. Set maximum read and write speeds

#### Smart Scheduling

Run operations during system idle time:

1. Go to Settings > Performance > Smart Scheduling
2. Enable smart scheduling
3. Set CPU usage threshold
4. Configure quiet hours

### Storage Efficiency

#### Deduplication

Save storage space by eliminating duplicate data:

1. Go to Settings > Storage > Deduplication
2. Enable deduplication
3. Choose deduplication method:
   - File-level: Faster, less granular
   - Block-level: Slower, more efficient
4. Click "Run Deduplication Now" to manually deduplicate snapshots

#### Compression

Further reduce storage usage with compression:

1. Go to Settings > Storage > Compression
2. Enable compression
3. Choose compression algorithm (zstd, lz4, or gzip)
4. Set compression level (higher = better compression but slower)

### Recovery Options

#### File-Level Restoration

Restore individual files without restoring the entire snapshot:

1. Right-click on a snapshot in the Snapshots panel
2. Select "Restore File"
3. Enter the path to the file within the snapshot
4. Specify the target path (optional)
5. Click "OK" to restore the file

#### Bootable Recovery Environment

Create a bootable recovery media:

1. Select a snapshot in the Snapshots panel
2. Click "Create Bootable Recovery"
3. Select the target device
4. Click "OK" to create the bootable media

#### Time Machine Browser

Browse snapshots across time:

1. Click "Time Machine" in the Snapshots panel
2. Navigate through snapshots using the timeline
3. Select files to restore
4. Click "Restore Selected" to restore the files

### User Interface

#### Dark Mode

Toggle between light and dark themes:

1. Click the moon icon in the header bar to toggle dark mode
2. Or go to Settings > UI > Theme to select a theme

#### Dashboard

The Dashboard provides an overview of your snapshots and system health:

- Total snapshots count
- Storage usage
- Space saved through deduplication
- Snapshot distribution
- Recent snapshots
- System health indicators

## Configuration

### Configuration File

SnapGuard's configuration is stored in a JSON file at `/etc/snapguard/config.json`. While it's recommended to use the Settings panel to modify the configuration, advanced users can edit this file directly.

### Important Configuration Options

- `snapshot.default_location`: Where snapshots are stored
- `snapshot.retention`: How many snapshots to keep
- `security.encryption`: Encryption settings
- `security.key_rotation`: Key rotation settings
- `security.mfa_policy`: Multi-factor authentication settings
- `performance.parallel_processing`: Parallel processing settings
- `performance.smart_scheduling`: Smart scheduling settings
- `storage.deduplication`: Deduplication settings
- `storage.compression`: Compression settings

## Troubleshooting

### Common Issues

#### Snapshot Creation Fails

**Possible causes:**
- Insufficient permissions
- Disk space issues
- BtrFS errors

**Solutions:**
1. Check that you have root privileges
2. Verify available disk space
3. Check BtrFS status with `btrfs filesystem show`

#### Encryption Issues

**Possible causes:**
- Missing encryption keys
- Corrupted metadata

**Solutions:**
1. Check that encryption keys exist in the key directory
2. Try restoring from a backup key
3. Check encryption metadata for errors

#### Deduplication Issues

**Possible causes:**
- Insufficient memory
- Filesystem errors

**Solutions:**
1. Reduce block size for block-level deduplication
2. Try file-level deduplication instead
3. Run filesystem check

### Logs

SnapGuard logs are stored in the following locations:

- Application logs: `/var/log/snapguard/snapguard.log`
- Audit logs: `/var/log/snapguard/audit.log`

## FAQ

### General Questions

**Q: Is SnapGuard compatible with my Linux distribution?**  
A: SnapGuard works with any Linux distribution that supports BtrFS and/or OverlayFS.

**Q: Can I use SnapGuard without a GUI?**  
A: Yes, SnapGuard provides a command-line interface as well.

**Q: How secure is the encryption?**  
A: SnapGuard uses industry-standard AES-256-GCM or ChaCha20-Poly1305 encryption, which are considered highly secure.

### Feature Questions

**Q: How much space can deduplication save?**  
A: This depends on your data. For typical system snapshots, deduplication can save 30-70% of space.

**Q: Can I restore individual files from encrypted snapshots?**  
A: Yes, SnapGuard can decrypt and restore individual files from encrypted snapshots.

**Q: How does key rotation work?**  
A: Key rotation creates new encryption keys while preserving access to data encrypted with old keys. Old keys are kept for decryption but marked as inactive.

**Q: What happens if I lose my encryption keys?**  
A: If you lose your encryption keys, you won't be able to decrypt your snapshots. It's recommended to back up your keys securely.

**Q: Can I use SnapGuard with external drives?**  
A: Yes, you can create and store snapshots on external drives as long as they use a supported filesystem.