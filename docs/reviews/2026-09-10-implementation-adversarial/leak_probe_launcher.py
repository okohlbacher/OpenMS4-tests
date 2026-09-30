"""Set the existing test's dependency fallback after launching Apple's leaks tool.

The signed system tool strips DYLD settings inherited at its own startup.
This launcher replaces itself with the test; it does not change dependencies.
"""
import os
import sys

os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = "/opt/homebrew/Cellar/abseil/20260107.1/lib"
os.execv(sys.argv[1], sys.argv[1:])
