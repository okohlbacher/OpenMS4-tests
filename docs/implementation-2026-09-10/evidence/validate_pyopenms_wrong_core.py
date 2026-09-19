"""Reject a compatible Core with altered provenance before Python domain imports."""
import json
import os
from pathlib import Path
import subprocess

workspace = Path(__file__).resolve().parents[1]
staging = workspace / "pyopenms-wheel-build/pyOpenMS"
provenance = json.loads((staging / "pyopenms/_build_provenance.json").read_text())
environment = {key: value for key, value in os.environ.items()
               if not key.startswith("DYLD_") and key not in ("OPENMS_DATA_PATH", "PYTHONPATH")}
environment.update(
    DYLD_LIBRARY_PATH=str(workspace / "wrong-core-identity-fixture"),
    DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/Cellar/abseil/20260107.1/lib",
    PYTHONPATH=str(staging), PYTHONDONTWRITEBYTECODE="1",
)
code = '''import sys
try:
    import pyopenms
except ImportError as error:
    assert "OpenMS runtime identity mismatch for source_revision" in str(error), error
    assert "0000000000000000000000000000000000000000" in str(error), error
    assert not any(name.startswith("pyopenms._pyopenms_") for name in sys.modules)
    print("REJECTED_WRONG_CORE_BEFORE_DOMAINS", error)
else:
    raise AssertionError("wrong Core library was accepted")
'''
result = subprocess.run(
    [str(workspace / "pyopenms-validation-venv/bin/python"), "-c", code],
    cwd="/private/tmp", env=environment, text=True, capture_output=True,
)
record = {
    "python_source_revision": provenance["source_revision"],
    "test": "actual compatible Core binary with wrong SHA rejected before domain imports",
    "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
}
(workspace / "implementation-build-evidence/pyopenms-final-wrong-core-runtime.json").write_text(
    json.dumps(record, indent=2) + "\n"
)
print(json.dumps(record, indent=2))
assert result.returncode == 0 and "REJECTED_WRONG_CORE_BEFORE_DOMAINS" in result.stdout
