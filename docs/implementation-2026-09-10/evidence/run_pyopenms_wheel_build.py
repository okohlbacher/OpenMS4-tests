"""Reproduce the authorized native Debug wheel build from an installed SDK."""
import os
from pathlib import Path
import shlex
import subprocess

workspace = Path(__file__).resolve().parents[1]
command = [
    str(workspace / "pyopenms-validation-venv/bin/python"), "-m", "build",
    str(workspace / "OpenMS4-tests/packages/pyopenms"), "--wheel", "--no-isolation",
    "--outdir", str(workspace / "pyopenms-wheel-final-raw"),
]
options = {
    "cmake.options.OpenMS_DIR": str(workspace / "product-sdk/lib/cmake/OpenMS"),
    "cmake.build_type": "Debug",
    "cmake.build_path": str(workspace / "pyopenms-wheel-build"),
    "cmake.generator": "Ninja",
    "cmake.options.PYOPENMS_PREPARE_WHEEL_REPAIR": "ON",
    "cmake.options.OPENMS4_REQUIRE_CLEAN_SOURCE": "ON",
    "cmake.options.CMAKE_PREFIX_PATH": "/opt/homebrew;/opt/homebrew/opt/libomp",
    "cmake.options.CURL_ROOT": "/opt/homebrew/opt/curl",
    "cmake.options.CMAKE_FIND_FRAMEWORK": "LAST",
    "cmake.options.Python_EXECUTABLE": str(workspace / "implementation-build-evidence/pyopenms-build-python"),
}
command.extend(f"-Coverride={key}={value}" for key, value in options.items())
environment = dict(os.environ, CMAKE_BUILD_PARALLEL_LEVEL="3",
                   DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/Cellar/abseil/20260107.1/lib",
                   PYTHONDONTWRITEBYTECODE="1")
environment.pop("OPENMS_DATA_PATH", None)
environment.pop("PYTHONPATH", None)
print(shlex.join(command), flush=True)
subprocess.run(command, env=environment, cwd=workspace, check=True)
