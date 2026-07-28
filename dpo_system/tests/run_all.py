from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    try:
        import pytest
    except ImportError:
        print("pytest is required. Install with: pip install pytest")
        return 2

    root = Path(__file__).resolve().parents[2]
    return pytest.main([str(root / "dpo_system" / "tests")])


if __name__ == "__main__":
    sys.exit(main())
