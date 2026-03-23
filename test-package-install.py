#!/usr/bin/env python3
"""
test-package-install.py
=======================
Test that the package metadata is valid and can be installed successfully.
Run: python test-package-install.py
"""
import subprocess
import sys
import json
from pathlib import Path

def main():
    print("=" * 70)
    print("📦 Testing package metadata and installation")
    print("=" * 70)

    # 1. Verify pyproject.toml exists and is valid
    print("\n[1/4] Checking pyproject.toml...")
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib
    
    pyproject = Path("pyproject.toml")
    if not pyproject.exists():
        print("❌ pyproject.toml not found")
        return False
    
    try:
        with open(pyproject, "rb") as f:
            config = tomllib.load(f)
        print(f"✓ pyproject.toml valid")
        print(f"  name: {config['project']['name']}")
        print(f"  version: {config['project']['version']}")
    except Exception as e:
        print(f"❌ Failed to parse pyproject.toml: {e}")
        return False

    # 2. Check required package directories
    print("\n[2/4] Checking package directories...")
    required_dirs = ["multi_agent", "single_agent"]
    for d in required_dirs:
        if not Path(d).is_dir():
            print(f"❌ Missing directory: {d}")
            return False
        print(f"✓ {d}/ exists")

    # 3. Test pip install . (build in isolation)
    print("\n[3/4] Testing pip install...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", "."],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode != 0:
            print(f"❌ pip install failed:\n{result.stderr}")
            return False
        print("✓ pip install -e . succeeded")
    except subprocess.TimeoutExpired:
        print("❌ pip install timed out")
        return False
    except Exception as e:
        print(f"❌ pip install error: {e}")
        return False

    # 4. Test package imports
    print("\n[4/4] Testing imports...")
    try:
        import multi_agent
        print("✓ import multi_agent")
    except ImportError as e:
        print(f"⚠ multi_agent import warning: {e}")
    
    try:
        import single_agent
        print("✓ import single_agent")
    except ImportError as e:
        print(f"⚠ single_agent import warning: {e}")

    try:
        from multi_agent.shared.ultrathink_core import Stage, TaskState
        print("✓ import multi_agent.shared.ultrathink_core")
    except ImportError as e:
        print(f"❌ Failed to import ultrathink_core: {e}")
        return False

    print("\n" + "=" * 70)
    print("✅ All package tests passed!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
