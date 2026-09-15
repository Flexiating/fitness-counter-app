#!/usr/bin/env bash
# Install or locate the Python version required by the source-code edition.
set -euo pipefail

if command -v python3.12 >/dev/null 2>&1; then
    echo "Python 3.12 is already installed: $(python3.12 --version)"
    echo "You can now run ../run_mac.sh"
    read -r -n 1 -s -p "Press any key to close..."
    echo
    exit 0
fi

echo "Fitness Counter needs Python 3.12 to run from source code."
echo

if command -v brew >/dev/null 2>&1; then
    read -r -p "Install Python 3.12 with Homebrew now? [Y/n] " answer
    if [[ "${answer:-Y}" =~ ^[Yy]$ ]]; then
        brew install python@3.12
        echo
        echo "Python 3.12 was installed. Close and reopen Terminal, then run ../run_mac.sh"
        read -r -n 1 -s -p "Press any key to close..."
        echo
        exit 0
    fi
fi

echo "Opening the official Python download page."
echo "Download and install Python 3.12, then run ../run_mac.sh"
open "https://www.python.org/downloads/"
read -r -n 1 -s -p "Press any key to close..."
echo
