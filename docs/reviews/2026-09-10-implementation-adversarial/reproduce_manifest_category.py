"""Configure TOPP with one missing metadata row using its existing mock-SDK test.

No source mutation or OpenMS build. CMake may run compiler-identification probes.
This intentionally confirms the audited
failure to reject incomplete tool metadata; it should fail after the fix.
"""
import json
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
sys.dont_write_bytecode = True
sys.path.insert(0, str(root / "tests"))
import test_consumer_configure as fixture

case = fixture.ConsumerConfigure()
case.setUp()
try:
    packages = case.root / "packages"
    source = packages / "topp"
    source.mkdir(parents=True)
    for path in (root / "packages/topp").iterdir():
        if path.name != "tools.json":
            (source / path.name).symlink_to(path, target_is_directory=path.is_dir())
    metadata = json.loads((root / "packages/topp/tools.json").read_text())
    omitted = "AssayGeneratorMetabo"
    metadata["tools"] = [row for row in metadata["tools"] if row["name"] != omitted]
    (source / "tools.json").write_text(json.dumps(metadata))
    fixture.PACKAGES = packages
    configured = case.configure("topp")
    assert configured.returncode == 0, configured.stdout + configured.stderr
    rows = (case.root / "build/share/openms4/tools/topp.tools.tsv").read_text().splitlines()
    prior = next(row for row in rows if row.startswith("AccurateMassSearch\t"))
    inherited = next(row for row in rows if row.startswith(omitted + "\t"))
    assert prior.split("\t")[1] == inherited.split("\t")[1]
    print(json.dumps(dict(configure_exit=configured.returncode, omitted_metadata=omitted,
                         previous_tool_row=prior, emitted_row=inherited,
                         scope="Actual TOPP CMake with controlled mock SDK; no OpenMS build; CMake compiler probes may run"), indent=2))
finally:
    case.tearDown()
