"""Small audit probes; no native build, application startup or real tool subprocesses.

Run with the OpenMS4-tests checkout as the first argument. These assertions
confirm the audited defects are present; they are not regression expectations.
"""
import ast
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace

root = Path(sys.argv[1]).resolve()
source = root / "packages/flashapp/src/workflow/CommandExecutor.py"
tree = ast.parse(source.read_text())
cls = next(node for node in tree.body if isinstance(node, ast.ClassDef))
methods = {node.name: node for node in cls.body if isinstance(node, ast.FunctionDef)}
scope = dict(threading=threading, time=time, subprocess=subprocess)
for name in ("run_multiple_commands", "run_command", "_stream_output"):
    exec(compile(ast.Module(body=[methods[name]], type_ignores=[]), str(source), "exec"), scope)
logs = []
logger = SimpleNamespace(log=lambda message, level: logs.append(message))
results = {}

def missing_command(command):
    raise FileNotFoundError("controlled missing executable")

errors = []
previous_hook = threading.excepthook
threading.excepthook = lambda args: errors.append(str(args.exc_value))
try:
    obj = SimpleNamespace(logger=logger, _get_max_threads=lambda: 2, run_command=missing_command)
    success = scope["run_multiple_commands"](obj, [["missing"], ["missing"]])
finally:
    threading.excepthook = previous_hook
assert success is True and len(errors) == 2
results["worker_exception"] = dict(reported_success=success, exceptions=errors)

logs.clear()
proc = SimpleNamespace(stdout=io.StringIO("out1\nout2\nout3\n"),
                       stderr=io.StringIO("err1\nerr2\nerr3\n"), poll=lambda: 1)
stderr = []
scope["_stream_output"](SimpleNamespace(logger=logger), proc, stderr)
assert stderr == ["err1"] and "out2" not in logs
results["completed_process_log_tail"] = dict(expected_stderr_lines=3, captured_stderr=stderr,
                                           captured_logs=list(logs))

class DeniedPID:
    def __truediv__(self, pid):
        return self

    def touch(self):
        raise PermissionError("controlled PID record failure")

cleanup = []
fake_process = SimpleNamespace(pid=123, wait=lambda: cleanup.append("wait"),
                               terminate=lambda: cleanup.append("terminate"))
scope["subprocess"] = SimpleNamespace(Popen=lambda *a, **kw: fake_process, PIPE=subprocess.PIPE)
try:
    scope["run_command"](SimpleNamespace(logger=logger, pid_dir=DeniedPID()), ["fake"])
except PermissionError:
    pass
else:
    raise AssertionError("expected injected PID failure")
assert cleanup == []
results["pid_failure_cleanup"] = dict(cleanup_calls=cleanup,
    limitation="Fake child proves missing cleanup path, not measured native heap leakage.")

with tempfile.TemporaryDirectory(prefix="openms4-audit-") as temp:
    temp = Path(temp)
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("artifact_verifier", root / "tools/verify_artifacts.py")
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    artifacts = temp / "artifacts"
    artifacts.mkdir()
    payload = b"controlled digest-valid payload"
    artifact = artifacts / "runtime.tar"
    artifact.write_bytes(payload)
    manifest = temp / "artifacts.lock.json"
    manifest.write_text(json.dumps(dict(schema_version=1, core_source_revision="b" * 40,
        artifacts=[dict(path=artifact.name, kind="runtime", sha256=hashlib.sha256(payload).hexdigest())])))
    verifier.verified_artifacts(manifest, artifacts)
    expected = json.loads((root / "packages/flashapp/dependencies.lock.json").read_text())["dependencies"]["OpenMS"]["source_revision"]
    assert expected != "b" * 40
    results["unbound_artifact_identity"] = dict(accepted="b" * 40, package_pin=expected,
        limitation="Manifest/hash verification only; archive extraction is a separate step.")

    share = temp / "sdk/share/OpenMS/4.0.0"
    (share / "test-data/core").mkdir(parents=True)
    (share / "test-data/core/audit-marker").write_text("test-only fixture")
    (share / "CHEMISTRY").mkdir()
    (share / "CHEMISTRY/unimod.xml").write_text("<fixture/>")
    cmake_source = (root / "packages/pyopenms/CMakeLists.txt").read_text()
    start = cmake_source.index("if(NOT NO_SHARE AND DEFINED OPENMS_SHARE_DIR")
    end = cmake_source.index("endif()", start) + len("endif()")
    copy = temp / "copy.cmake"
    build = temp / "python-build"
    copy.write_text(f'set(OPENMS_SHARE_DIR "{share}")\nset(PYOPENMS_BUILD_DIR "{build}")\n' + cmake_source[start:end])
    subprocess.run(["cmake", "-P", str(copy)], check=True, capture_output=True)
    bundled = build / "pyopenms/share/OpenMS/test-data/core/audit-marker"
    assert bundled.is_file()
    results["wheel_fixture_copy"] = dict(copied_test_only_fixture=True,
        method="Exact production CMake copy block, isolated marker SDK; no wheel built.")

print(json.dumps(results, indent=2))
