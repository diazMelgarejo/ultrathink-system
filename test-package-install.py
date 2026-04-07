#!/usr/bin/env python3
"""
test-package-install.py
=======================
Test that the package metadata is valid, builds locally, and can be installed
from a built wheel without relying on network access.
Run: python test-package-install.py
"""
import importlib.util
import os
import subprocess
import sys
import tempfile
import venv
import zipfile
from pathlib import Path


def run_command(cmd, *, timeout=120, env=None):
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )


def in_venv_python(venv_dir: Path) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def missing_modules(*module_names):
    return [name for name in module_names if importlib.util.find_spec(name) is None]


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
        print(f"  build backend: {config['build-system']['build-backend']}")
    except Exception as e:
        print(f"❌ Failed to parse pyproject.toml: {e}")
        return False

    # 2. Check required package directories
    print("\n[2/4] Checking package directories...")
    required_dirs = ["bin"]
    for d in required_dirs:
        if not Path(d).is_dir():
            print(f"❌ Missing directory: {d}")
            return False
        print(f"✓ {d}/ exists")

    # 3. Preflight and build locally without networked build isolation.
    print("\n[3/4] Building distribution artifacts...")
    missing = missing_modules("pip", "build", "venv")
    if missing:
        print("❌ Missing required local tooling: " + ", ".join(missing))
        print("   Use an environment with pip, build, and venv available.")
        print("   Example: ./.venv-test-install/bin/python test-package-install.py")
        return False

    try:
        result = run_command([sys.executable, "-m", "build", "--no-isolation"], timeout=180)
    except subprocess.TimeoutExpired:
        print("❌ local build timed out")
        return False

    if result.returncode != 0:
        print("❌ local build failed:")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return False

    wheel_candidates = sorted(Path("dist").glob("ultrathink_system-*.whl"))
    if not wheel_candidates:
        print("❌ Build completed but no wheel was produced in dist/")
        return False
    wheel_path = wheel_candidates[-1]
    print(f"✓ built wheel: {wheel_path.name}")
    with zipfile.ZipFile(wheel_path) as wheel_zip:
        wheel_entries = set(wheel_zip.namelist())
    if "api_server.py" not in wheel_entries:
        print("❌ wheel is missing api_server.py")
        return False
    print("✓ wheel includes api_server.py")

    # 4. Install the built wheel into an isolated temp venv and test imports.
    print("\n[4/4] Installing built wheel and testing imports...")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            venv_dir = Path(temp_dir) / "install-check"
            venv.EnvBuilder(with_pip=True, clear=True).create(venv_dir)
            python_bin = in_venv_python(venv_dir)

            install_result = run_command(
                [str(python_bin), "-m", "pip", "install", "--no-deps", str(wheel_path)],
                timeout=180,
                env={**os.environ, "PIP_DISABLE_PIP_VERSION_CHECK": "1"},
            )
            if install_result.returncode != 0:
                print("❌ wheel install failed:")
                if install_result.stdout:
                    print(install_result.stdout)
                if install_result.stderr:
                    print(install_result.stderr)
                return False
            print(f"✓ installed wheel into temp venv: {wheel_path.name}")

            import_result = run_command(
                [
                    str(python_bin),
                    "-c",
                    (
                        "import bin; "
                        "from bin.shared.ultrathink_core import Stage, TaskState; "
                        "from bin.skills.cidf.core.content_insertion_framework import decide; "
                        "print('imports ok')"
                    ),
                ],
                timeout=60,
            )
            if import_result.returncode != 0:
                print("❌ import verification failed:")
                if import_result.stdout:
                    print(import_result.stdout)
                if import_result.stderr:
                    print(import_result.stderr)
                return False
            print("✓ import bin")
            
            print("✓ import bin.shared.ultrathink_core")
            print("✓ import bin.skills.cidf.core.content_insertion_framework")
    except subprocess.TimeoutExpired:
        print("❌ install or import verification timed out")
        return False

    print("\n" + "=" * 70)
    print("✅ All package tests passed!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
