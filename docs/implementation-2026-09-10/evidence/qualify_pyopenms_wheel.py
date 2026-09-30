"""Run the installed wheel's full suite with development inputs inaccessible."""
import json
import os
from pathlib import Path
import subprocess
import sys

workspace = Path(__file__).resolve().parents[1]
qualification = workspace / "pyopenms-wheel-tests"
denied = [
    workspace / "OpenMS4-tests/packages/core", workspace / "core-build",
    workspace / "OpenMS4-tests/packages/pyopenms", workspace / "pyopenms-wheel-build",
    workspace / "product-sdk", workspace / "core-sdk", workspace / "cli-build",
    Path("/opt/homebrew"), Path("/Users/kohlbach/OpenMS"),
]
profile = "(version 1)\n(allow default)\n" + "\n".join(
    f"(deny file-read* (subpath {json.dumps(str(path))}))" for path in denied
)
(workspace / "implementation-build-evidence/pyopenms-wheel-sandbox.sb").write_text(profile + "\n")
environment = {key: value for key, value in os.environ.items()
               if not key.startswith("DYLD_") and key not in ("OPENMS_DATA_PATH", "PYTHONPATH")}
environment.update(
    PYTHONDONTWRITEBYTECODE="1", OMP_NUM_THREADS="2", MPLBACKEND="Agg",
    MPLCONFIGDIR=str(qualification / "matplotlib-cache"),
    OPENMS_CLASS_TEST_DATA_PATH=str(qualification / "fixtures/core"),
    OPENMS_TEST_DATA_PATH=str(qualification / "fixtures/topp"),
)
code = """
import errno, json, os, pathlib, sys
root = pathlib.Path(sys.argv[1])
for path in (root/'product-sdk/lib/libOpenMS.dylib',
             root/'OpenMS4-tests/packages/core/CMakeLists.txt',
             root/'OpenMS4-tests/packages/pyopenms/CMakeLists.txt',
             pathlib.Path('/opt/homebrew/include/arrow/api.h')):
    try:
        path.open('rb').close()
    except OSError as error:
        assert error.errno in (errno.EPERM, errno.EACCES), (path, error)
    else:
        raise AssertionError(f'development input remained readable: {path}')
assert not any(key.startswith('DYLD_') for key in os.environ)
assert 'OPENMS_DATA_PATH' not in os.environ
import pyopenms as oms
assert oms.__source_revision__ == '14d950a460636b9a8fa255b7ac657926fec403de'
assert oms.__source_dirty__ is False
assert oms.__openms_core_revision__ == '4fdec46b205459b92e7d3b9e56df5d8e912d5c85'
assert pathlib.Path(oms.__file__).is_relative_to(root/'pyopenms-wheel-venv')
assert pathlib.Path(oms.File.getOpenMSDataPath()) == pathlib.Path(oms.__file__).parent/'share/OpenMS'
print('REPAIRED_WHEEL_IMPORTED_WITH_DEVELOPMENT_READS_DENIED', flush=True)
print(json.dumps({'wheel': oms.__file__, 'data': oms.File.getOpenMSDataPath(),
                  'core': oms.__openms_runtime_build_info__}), flush=True)
import pytest
raise SystemExit(pytest.main([
    str(root/'pyopenms-wheel-tests/tests'), '--import-mode=importlib', '-q', '-ra',
    '--junitxml=' + str(root/'implementation-build-evidence/pyopenms-final-wheel-tests.xml'),
]))
"""
command = ["/usr/bin/sandbox-exec", "-p", profile,
           str(workspace / "pyopenms-wheel-venv/bin/python"), "-u", "-c", code, str(workspace)]
result = subprocess.run(command, cwd=qualification, env=environment)
sys.exit(result.returncode)
