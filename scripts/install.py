"""Install dependencies for the streaming-platform workspace.

This script is intentionally minimal for foundation stage.
"""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REQ = ROOT / "requirements" / "development.txt"


def main() -> int:
    if not REQ.exists():
        print(f"Requirements file not found: {REQ}")
        return 1

    cmd = [sys.executable, "-m", "pip", "install", "-r", str(REQ)]
    print("Running:", " ".join(cmd))
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
