#!/usr/bin/env python3
"""WalletMonitor CLI entry point"""

import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scripts.cli import main

if __name__ == "__main__":
    main()
