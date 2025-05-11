#!/usr/bin/env python3

import sys
import logging
from snapguard import SnapGuard

def main():
    # load configuration
    snapguard = SnapGuard()
    
    # create snapshot
    try:
        success = snapguard.create_snapshot("automatisch")
        if not success:
            logging.error("Automatische Snapshot-Erstellung fehlgeschlagen")
            sys.exit(1)
    except Exception as e:
        logging.error(f"Fehler bei der automatischen Snapshot-Erstellung: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 