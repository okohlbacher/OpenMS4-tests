"""Build a deliberately mismatched, ABI-compatible Core identity fixture on macOS.

Reuse the tested Core objects; replace only VersionInfo's generated source identity.
Never alter production source, build outputs or installed libraries.
"""
import json
import os
from pathlib import Path
import shlex
import subprocess

workspace = Path(__file__).resolve().parents[1]
build = workspace / 'core-build'
output = workspace / 'wrong-core-identity-fixture'
output.mkdir(exist_ok=True)
headers = output / 'include/OpenMS'
headers.mkdir(parents=True, exist_ok=True)
info = json.loads((build / 'identity/Debug/OpenMSBuildInfo.json').read_text())
old_revision = info['source_revision']
new_revision = '0' * 40
header = build / 'identity/Debug/OpenMS/openms_build_info.h'
(headers / header.name).write_text(header.read_text().replace(old_revision, new_revision))
fixture_json = (build / 'identity/Debug/OpenMSBuildInfo.json').read_text().replace(old_revision, new_revision)
(output / 'OpenMSBuildInfo.json').write_text(fixture_json)
row = next(row for row in json.loads((build / 'compile_commands.json').read_text())
           if row['file'].endswith('/CONCEPT/VersionInfo.cpp'))
compile_args = row.get('arguments') or shlex.split(row['command'])
original_object = compile_args[compile_args.index('-o') + 1]
compile_args[compile_args.index('-o') + 1] = str(output / 'VersionInfo.o')
compile_args.insert(1, '-I' + str(output / 'include'))
commands = subprocess.check_output(['ninja', '-C', str(build), '-t', 'commands', 'OpenMS'], text=True)
link = next(shlex.split(line) for line in reversed(commands.splitlines())
            if '-dynamiclib' in line and '-o lib/libOpenMS.dylib ' in line)
assert link[:2] == [':', '&&'] and link[-2:] == ['&&', ':']
link = link[2:-2]
assert '&&' not in link
link[link.index('-o') + 1] = str(output / 'libOpenMS.dylib')
link[link.index(original_object)] = str(output / 'VersionInfo.o')
records = []

def run(args, expected, stem, env=None):
    result = subprocess.run(args, cwd=build, env=env, capture_output=True, text=True)
    (output / (stem + '.log')).write_text(result.stdout + result.stderr)
    records.append({'command': args, 'expected_exit': expected, 'exit_code': result.returncode})
    (output / 'results.json').write_text(json.dumps(records, indent=2) + '\n')
    if result.returncode != expected:
        raise SystemExit(f'{stem} failed: see {output / (stem + ".log")}')

run(compile_args, 0, 'compile')
run(link, 0, 'link')
env = dict(os.environ, DYLD_LIBRARY_PATH=str(output),
           DYLD_FALLBACK_LIBRARY_PATH='/opt/homebrew/Cellar/abseil/20260107.1/lib')
probe = str(workspace / 'installed-core-implementation/original-consumer/sdk_identity')
# The alternate identity passes its own complete JSON; this proves it loaded and ran.
run([probe, str(output / 'OpenMSBuildInfo.json'), new_revision, '0'], 0, 'fixture-positive', env)
run([probe, str(build / 'identity/Debug/OpenMSBuildInfo.json'), old_revision, '0'], 3, 'expected-mismatch', env)
print(f'Compatible swapped-library identity test passed: {output}')
