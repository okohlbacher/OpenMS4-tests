#!/usr/bin/env python3
"""Instrument the unchanged production VersionInfo TU and concurrent identity probe only."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

WORKSPACE = Path(__file__).resolve().parents[1]
BUILD = WORKSPACE / 'core-build'
OUTPUT = Path(__file__).resolve().parent
SOURCE = WORKSPACE / 'OpenMS4-tests/packages/core'
rows = json.loads((BUILD / 'compile_commands.json').read_text())
version = next(row for row in rows if row['file'].endswith('/CONCEPT/VersionInfo.cpp'))
probe = next(row for row in rows if row['file'].endswith('/installed_sdk_acceptance/identity.cpp'))
commands = subprocess.check_output(['ninja', '-C', str(BUILD), '-t', 'commands', 'CoreIdentity_probe'], text=True)
link = next(shlex.split(line) for line in reversed(commands.splitlines())
            if '-o src/tests/class_tests/bin/CoreIdentity_probe ' in line)
# Ninja's link rule wraps a single compiler invocation in ': && ... && :'.
if link[:2] == [':', '&&']:
    link = link[2:]
if link[-2:] == ['&&', ':']:
    link = link[:-2]
assert '&&' not in link, link
info_file = BUILD / 'identity/Debug/OpenMSBuildInfo.json'
info = json.loads(info_file.read_text())
env = os.environ.copy()
# This machine's re2 binary still requires the installed older Abseil runtime.
compatibility = Path('/opt/homebrew/Cellar/abseil/20260107.1/lib')
if compatibility.is_dir():
    env['DYLD_FALLBACK_LIBRARY_PATH'] = str(compatibility)

previous = json.loads((OUTPUT / 'results.json').read_text()) if (OUTPUT / 'results.json').exists() else {}
source_hash = hashlib.sha256(Path(version['file']).read_bytes()).hexdigest()
if previous.get('source_revision') != info['source_revision'] or previous.get('source_sha256') != source_hash:
    previous = {}

report = {
    'scope': 'Production VersionInfo.cpp and the concurrent identity probe are instrumented. Other Core/dependency translation units are not.',
    'source_revision': info['source_revision'],
    'source_dirty': info['source_dirty'],
    'source_sha256': source_hash,
    'probe_sha256': hashlib.sha256(Path(probe['file']).read_bytes()).hexdigest(),
    'loaded_dependency_workaround': env.get('DYLD_FALLBACK_LIBRARY_PATH'),
    'profiles': previous.get('profiles', {}),
}

def run(command, stem, environment=None):
    started = time.monotonic()
    try:
        result = subprocess.run(command, cwd=BUILD, env=environment or env,
                                capture_output=True, text=True, timeout=180)
        record = {'command': command, 'exit_code': result.returncode,
                  'elapsed_seconds': round(time.monotonic() - started, 3)}
        (OUTPUT / (stem + '.stdout')).write_text(result.stdout)
        (OUTPUT / (stem + '.stderr')).write_text(result.stderr)
        return record
    except subprocess.TimeoutExpired as error:
        return {'command': command, 'timeout_seconds': error.timeout}

def compile_command(row, output, flags):
    original = row.get('arguments') or shlex.split(row['command'])
    command = []
    skip = False
    for argument in original:
        if skip:
            skip = False
            continue
        if argument in ('-o', '-MF', '-MT', '-MQ'):
            skip = True
        elif argument not in ('-MD', '-MMD'):
            command.append(argument)
    return [*command, *flags, '-o', str(output)]

for name, flags in [('tsan', ['-fsanitize=thread', '-fno-omit-frame-pointer']),
                    ('asan-ubsan', ['-fsanitize=address,undefined', '-fno-sanitize-recover=all', '-fno-omit-frame-pointer']),
                    ('coverage', ['-fprofile-instr-generate', '-fcoverage-mapping', '-fprofile-update=atomic'])]:
    if sys.argv[1:] and name not in sys.argv[1:]:
        continue
    directory = OUTPUT / name
    directory.mkdir(exist_ok=True)
    records = []
    objects = [directory / 'VersionInfo.o', directory / 'identity.o']
    for row, obj in zip((version, probe), objects):
        record = run(compile_command(row, obj, flags), name + '-' + obj.stem + '-compile')
        records.append(record)
        if record.get('exit_code') != 0:
            break
    if len(records) == 2 and all(record.get('exit_code') == 0 for record in records):
        command = list(link)
        object_index = next(i for i, arg in enumerate(command) if arg.endswith('/identity.cpp.o'))
        command[object_index:object_index + 1] = list(map(str, objects))
        command[command.index('-o') + 1] = str(directory / 'identity')
        command.extend(flags)
        records.append(run(command, name + '-link'))
        if records[-1].get('exit_code') == 0:
            runtime_env = dict(env)
            if name == 'coverage':
                runtime_env['LLVM_PROFILE_FILE'] = str(directory / 'identity.profraw')
            if name == 'tsan':
                runtime_env['TSAN_OPTIONS'] = 'halt_on_error=1'
            records.append(run([str(directory / 'identity'), str(info_file), info['source_revision'],
                                '1' if info['source_dirty'] else '0'], name + '-run', runtime_env))
    report['profiles'][name] = records
    (OUTPUT / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
    print(name, [(record.get('exit_code'), record.get('timeout_seconds')) for record in records], flush=True)

coverage = report['profiles']['coverage']
if len(coverage) == 4 and all(record.get('exit_code') == 0 for record in coverage):
    profdata = subprocess.check_output(['xcrun', '--find', 'llvm-profdata'], text=True).strip()
    cov = subprocess.check_output(['xcrun', '--find', 'llvm-cov'], text=True).strip()
    directory = OUTPUT / 'coverage'
    records = [run([profdata, 'merge', '-sparse', str(directory / 'identity.profraw'), '-o', str(directory / 'identity.profdata')], 'coverage-merge')]
    records.append(run([cov, 'export', str(directory / 'identity'), '-instr-profile=' + str(directory / 'identity.profdata'), version['file']], 'coverage-export'))
    records.append(run([cov, 'show', str(directory / 'identity'), '-instr-profile=' + str(directory / 'identity.profdata'), '-show-branches=count', version['file']], 'coverage-lines'))
    report['coverage_reports'] = records
    (OUTPUT / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
