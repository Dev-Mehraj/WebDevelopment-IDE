#!/usr/bin/env python3
"""
Secure Build Script for WebDevelopmentIDE.py
Uses PyInstaller to create standalone executable
"""

import os
import subprocess
import sys


def build_with_pyinstaller():
    """
    Build using PyInstaller - Creates standalone executable
    """
    print("=" * 60)
    print("Building WebDevelopmentIDE with PyInstaller")
    print("=" * 60)

    # Create dist directory if it doesn't exist
    os.makedirs("dist", exist_ok=True)
    print("\n📁 Output directory: dist/\n")

    pyinstaller_cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--noconsole",
        "--windowed",
        # Icon and name
        "--icon=icon.ico",
        "--name=WebDevelopmentIDE",
        # Add data files
        "--add-data",
        "splash.png;.",
        "--add-data",
        "icon.ico;.",
        # Output directories
        "--distpath=dist",
        "--workpath=build",
        "--specpath=.",
        # Hidden imports (if needed)
        "--hidden-import=PySide6",
        "--hidden-import=ollama",
        # Clean up
        "--clean",
        "WebDevelopmentIDE.py",
    ]

    try:
        print("\nStarting PyInstaller build...")
        print("This may take 2-5 minutes...\n")

        result = subprocess.run(pyinstaller_cmd, check=True)

        print("\n" + "=" * 60)
        print("✓ Build successful!")
        print("=" * 60)
        print("\n📦 Your executable: dist\\WebDevelopmentIDE.exe")
        print("\nFeatures:")
        print("  ✓ Standalone executable (no Python required)")
        print("  ✓ Bytecode embedded and protected")
        print("  ✓ All dependencies bundled")
        print("  ✓ Icon and splash screen embedded")
        print("\n✨ Main directory kept clean - all build files in dist/")

        return True

    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


def install_dependencies():
    """Install required build tools"""
    print("Installing PyInstaller...\n")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    print("\n✓ PyInstaller installed!")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("BUILD TOOL FOR WEB DEVELOPMENT IDE")
    print("=" * 60)

    print("\nChoose option:")
    print("1. Build executable")
    print("2. Install PyInstaller first")
    print("3. Exit")

    choice = input("\nEnter choice (1-3): ").strip()

    if choice == "1":
        print("\nChecking PyInstaller installation...")
        try:
            subprocess.run(
                [sys.executable, "-m", "PyInstaller", "--version"],
                check=True,
                capture_output=True,
            )
        except:
            print("PyInstaller not found. Installing...")
            install_dependencies()

        build_with_pyinstaller()

    elif choice == "2":
        install_dependencies()

    elif choice == "3":
        print("Exiting...")
        sys.exit(0)

    else:
        print("Invalid choice!")
        sys.exit(1)
    """
    Build using Nuitka - Compiles Python to C/C++ machine code
    Most secure option - nearly impossible to reverse engineer
    """
    print("=" * 60)
    print("Building with Nuitka (Maximum Security)")
    print("=" * 60)

    # Create dist directory if it doesn't exist
    os.makedirs("dist", exist_ok=True)
    print("\n📁 Output directory: dist/\n")

    # Nuitka command with security options
    nuitka_cmd = [
        sys.executable,
        "-m",
        "nuitka",
        # Output options
        "--mode=onefile",  # Single executable file (includes standalone)
        "--msvc=latest",  # Force MSVC compiler (required for Python 3.13+)
        "--output-dir=dist",  # Output to dist subfolder
        # Windows-specific options
        "--windows-icon-from-ico=icon.ico",
        "--windows-console-mode=disable",  # No console window
        "--company-name=WebDevelopmentIDE",
        "--product-name=Web Development IDE",
        "--file-version=1.0.0.0",
        "--product-version=1.0.0.0",
        "--file-description=Professional Web Development IDE",
        # Include data files
        "--include-data-files=splash.png=splash.png",
        "--include-data-files=icon.ico=icon.ico",
        # PySide6 plugin (required)
        "--enable-plugin=pyside6",
        # Optimization and obfuscation
        "--remove-output",  # Remove build directory after compilation
        "--assume-yes-for-downloads",
        # Advanced protection options
        "--lto=yes",  # Link Time Optimization (makes it harder to analyze)
        # Output name
        "--output-filename=WebDevelopmentIDE.exe",
        # Source file
        "WebDevelopmentIDE.py",
    ]

    try:
        print("\nStarting Nuitka compilation...")
        print("This may take 5-15 minutes depending on your system...\n")

        result = subprocess.run(nuitka_cmd, check=True)

        print("\n" + "=" * 60)
        print("✓ Build successful!")
        print("=" * 60)
        print("\n📦 Your secure executable: dist\\WebDevelopmentIDE.exe")
        print("\nSecurity features enabled:")
        print("  ✓ Compiled to native machine code (C/C++)")
        print("  ✓ No Python bytecode (cannot be decompiled)")
        print("  ✓ Link Time Optimization enabled")
        print("  ✓ Standalone executable (no Python required)")
        print("  ✓ Icon and splash screen embedded")
        print("\n✨ Main directory kept clean - all build files in dist/")

        return True

    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


def build_with_pyinstaller_advanced():
    """
    Alternative: PyInstaller with advanced obfuscation
    Good protection but not as secure as Nuitka
    """
    print("=" * 60)
    print("Building with PyInstaller (Advanced Protection)")
    print("=" * 60)

    pyinstaller_cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        # Use spec file for advanced options
        "--onefile",
        "--noconsole",
        "--windowed",
        # Icon and name
        "--icon=icon.ico",
        "--name=WebDevIDE",
        # Add data files
        "--add-data",
        "splash.png;.",
        "--add-data",
        "icon.ico;.",
        # Obfuscation options
        "--key=YOUR_ENCRYPTION_KEY_HERE_32_CHARS",  # AES encryption
        # Strip symbols and optimize
        "--strip",
        # Hidden imports (if needed)
        "--hidden-import=PySide6",
        "--hidden-import=ollama",
        # Clean up
        "--clean",
        "WebDevelopmentIDE.py",
    ]

    try:
        print("\nStarting PyInstaller build...")
        result = subprocess.run(pyinstaller_cmd, check=True)

        print("\n" + "=" * 60)
        print("✓ Build successful!")
        print("=" * 60)
        print("\nYour executable: dist\\WebDevIDE.exe")

        return True

    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed: {e}")
        return False


def install_dependencies():
    """Install required build tools"""
    print("Installing build dependencies...\n")

    dependencies = [
        "nuitka",
        "ordered-set",
        "zstandard",
    ]

    for dep in dependencies:
        print(f"Installing {dep}...")
        subprocess.run([sys.executable, "-m", "pip", "install", dep])

    print("\n✓ Dependencies installed!")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("SECURE BUILD TOOL FOR WEB DEVELOPMENT IDE")
    print("=" * 60)

    print("\nChoose build method:")
    print("1. Nuitka (Recommended - Maximum Security)")
    print("2. PyInstaller with Encryption")
    print("3. Install dependencies first")
    print("4. Exit")

    choice = input("\nEnter choice (1-4): ").strip()

    if choice == "1":
        print("\nChecking Nuitka installation...")
        try:
            subprocess.run(
                [sys.executable, "-m", "nuitka", "--version"],
                check=True,
                capture_output=True,
            )
        except:
            print("Nuitka not found. Installing...")
            install_dependencies()

        build_with_nuitka()

    elif choice == "2":
        build_with_pyinstaller_advanced()

    elif choice == "3":
        install_dependencies()

    elif choice == "4":
        print("Exiting...")
        sys.exit(0)

    else:
        print("Invalid choice!")
