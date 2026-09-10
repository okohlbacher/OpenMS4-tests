"""Bundle the existing installed dependency closure with standard delocate."""
import os
from pathlib import Path
import sys

from delocate.cmd.delocate_wheel import main

workspace = Path(__file__).resolve().parents[1]
os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = "/opt/homebrew/Cellar/abseil/20260107.1/lib"
sys.argv = [
    "delocate-wheel", "--require-archs", "arm64", "-v", "--wheel-dir",
    str(workspace / "pyopenms-wheel-final-repaired"),
    str(workspace / "pyopenms-wheel-final-raw/pyopenms-4.0.0.dev0-cp312-cp312-macosx_11_0_arm64.whl"),
]
main()
