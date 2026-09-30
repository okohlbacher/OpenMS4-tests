#!/usr/bin/env python3
"""Run source/configuration checks without compiling OpenMS or native products."""
from pathlib import Path
import subprocess
import os
import sys

root = Path(__file__).resolve().parents[1]
checks = [
    (root, [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v']),
    (root/'packages/core', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests/sdk_contract', '-v']),
    (root/'packages/core', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests/installed_sdk_acceptance', '-v']),
    (root/'packages/test-data', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v']),
    (root/'packages/flash', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v']),
    (root/'packages/nuxl', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v']),
    (root/'packages/prose', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v']),
    (root/'packages/desktop', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_source_boundaries.py', '-v']),
    (root/'packages/pyopenms', [sys.executable, 'tools/check_standalone.py']),
    (root/'packages/pyopenms', [sys.executable, 'tools/check_cmake_contract.py']),
]
for directory, command in checks:
    print(f'Checking {directory.relative_to(root) or "."}', flush=True)
    subprocess.run(command, cwd=directory, check=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
print('All source/configuration checks passed. This command does not run native compilation or numerical tests.')
