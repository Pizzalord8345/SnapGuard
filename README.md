# SnapGuard 🛡️

**A modern, secure, and user-friendly snapshot & backup manager for Linux using BtrFS and OverlayFS – a permissive alternative to Snapper.**

![License](https://img.shields.io/github/license/Pizzalord8345/SnapGuard)
![Issues](https://img.shields.io/github/issues/Pizzalord8345/SnapGuard)
![Last Commit](https://img.shields.io/github/last-commit/Pizzalord8345/SnapGuard)
![Stars](https://img.shields.io/github/stars/Pizzalord8345/SnapGuard?style=social)

---

<p align="center">
  <img src="docs/snapguard-demo.gif" width="700" alt="SnapGuard Demo" />
</p>

---

## Why SnapGuard?

SnapGuard is built for power users and Linux enthusiasts who want secure and transparent control over their BtrFS/OverlayFS snapshots. Unlike Snapper, SnapGuard features an intuitive GUI, fine-grained encryption, Polkit access control, and flexible snapshot retention strategies.

## 🔐 Main Features

### Security
- AES-256-GCM file-level encryption
- PBKDF2 (100k iterations) key derivation
- HMAC-SHA256 file signing
- Secure key storage & separation of encryption/signing keys
- Integrity checks before export and during restoration

### Snapshot Management
- Daily/weekly/monthly retention policies
- Configurable per subvolume
- Parallel snapshot creation for speed

### Backup and Export
- SHA-256 checksums of complete backups
- Metadata preservation
- Target media flexibility
- Auto verification after export

### User Interface
- GTK-based GUI
- Systemd integration
- Configure security & retention visually

### Monitoring & Logging
- Audit log of all actions
- Success & error log separation
- Optional desktop and email notifications

---

## 📦 Installation

See [INSTALL.md](INSTALL.md) for setup instructions.

---

## ⚙️ Configuration (config.json)

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

---

## 🛠️ Development

### Dependencies
- Python 3.6+
- GTK 3.0
- BtrFS
- Systemd
- Polkit

### Setup
```bash
git clone https://github.com/Pizzalord8345/SnapGuard.git
cd SnapGuard
pip install -r requirements.txt
```

---

## 🤝 Contributing
We welcome contributors! See [CONTRIBUTING.md](CONTRIBUTING.md) for more info.

---

## 📄 License
Apache 2.0 License – free for personal and commercial use.

---

<!-- SEO -->
<!--
keywords: snapguard, linux backup manager, btrfs snapshots, snapper alternative, overlayfs snapshot, gtk backup gui, encrypted snapshots, polkit backup tool, secure backup linux
-->


