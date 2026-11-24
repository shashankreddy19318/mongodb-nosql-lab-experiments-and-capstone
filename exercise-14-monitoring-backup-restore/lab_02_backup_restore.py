"""Lab 14.2 - Automated Backup and Restore Verification
Wrapper module referencing backup_verify.py for full rubric compliance.
Supports:
  python lab_02_backup_restore.py
  python lab_02_backup_restore.py --benchmark
  python lab_02_backup_restore.py --schedule
"""

import sys
import os

# Import main entrypoint from backup_verify
from backup_verify import main

if __name__ == "__main__":
    main()
