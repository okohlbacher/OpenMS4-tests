#!/usr/bin/env python3
"""Validate installed desktop products under an explicit source/build read-denial profile."""
import json
import os
from pathlib import Path
import subprocess
import shutil
import time

WORKSPACE = Path(__file__).resolve().parents[1]
EVIDENCE = Path(__file__).resolve().parent
SDK = WORKSPACE / 'desktop-relocated-sdk-b392300'
FIXTURES = EVIDENCE / 'desktop-fixtures'
OUTPUT = EVIDENCE / 'desktop-relocated-output'
if OUTPUT.exists():
    shutil.rmtree(OUTPUT)
OUTPUT.mkdir()
denied = [WORKSPACE / name for name in ('OpenMS4-tests', 'core-build', 'cli-build', 'topp-build',
          'flash-build', 'desktop-gui-build', 'desktop-viewers-build', 'desktop-workflows-build',
          'product-sdk', 'core-sdk')]
profile = '(version 1)(allow default)' + ''.join(
    '(deny file-read* (subpath ' + json.dumps(str(path)) + '))' for path in denied)
(EVIDENCE / 'desktop-isolation.sb').write_text(profile + '\n')
base = os.environ.copy()
for key in ('OPENMS_DATA_PATH', 'OPENMS_TOOL_PREFIX_PATH', 'DYLD_LIBRARY_PATH',
            'DYLD_FALLBACK_LIBRARY_PATH', 'LD_LIBRARY_PATH', 'QT_PLUGIN_PATH'):
    base.pop(key, None)
settings = ['QT_QPA_PLATFORM=offscreen', 'OPENMS_DISABLE_UPDATE_CHECK=ON',
            'DYLD_PRINT_LIBRARIES=1', 'OMP_NUM_THREADS=2',
            'OPENMS_TOOL_PREFIX_PATH=' + str(SDK),
            'DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/Cellar/abseil/20260107.1/lib']
records = []

def run(name, command, expected=0, diagnostic=None, extra=(), verify_libraries=True):
    # env sets test-only variables after entering the stricter sandbox (SIP clears
    # inherited DYLD variables when launching protected Apple executables).
    argv = ['sandbox-exec', '-p', profile, '/usr/bin/env', *settings, *extra, *map(str, command)]
    started = time.monotonic()
    result = subprocess.run(argv, cwd=OUTPUT, env=base, capture_output=True, text=True, timeout=180)
    (EVIDENCE / ('desktop-relocated-' + name + '.stdout')).write_text(result.stdout)
    (EVIDENCE / ('desktop-relocated-' + name + '.stderr')).write_text(result.stderr)
    record = {'name': name, 'command': argv, 'exit_code': result.returncode,
              'expected_exit_code': expected, 'elapsed_seconds': round(time.monotonic() - started, 3)}
    record['passed'] = result.returncode == expected and (
        diagnostic is None or diagnostic in result.stdout + result.stderr)
    libraries = []
    if verify_libraries:
        for line in result.stderr.splitlines():
            if '> ' in line:
                path = Path(line.split('> ', 1)[1])
                if path.name.startswith(('libOpenMS', 'libOpenSwathAlgo')):
                    libraries.append(str(path.resolve()))
        record['loaded_openms_libraries'] = sorted(set(libraries))
        record['passed'] &= bool(libraries) and all(Path(path).is_relative_to(SDK) for path in libraries)
    records.append(record)
    (EVIDENCE / 'desktop-relocation-results.json').write_text(json.dumps(records, indent=2) + '\n')
    if not record['passed']:
        raise RuntimeError(f'{name} failed; see recorded stdout/stderr')
    return result

run('isolation-rejects-source', ['/bin/cat', WORKSPACE / 'OpenMS4-tests/packages/core/CMakeLists.txt'],
    expected=1, diagnostic='Operation not permitted', verify_libraries=False)
for name in ('TOPPView', 'TOPPAS', 'INIFileEditor', 'ImageCreator', 'ExecutePipeline'):
    executable = SDK / 'bin' / (name + '.app/Contents/MacOS/' + name if name in ('TOPPView', 'TOPPAS', 'INIFileEditor') else name)
    run(name + '-help', [executable, '--help'], diagnostic=name)
run('embedded-style-startup', [SDK / 'bin/TOPPView.app/Contents/MacOS/TOPPView', '--acceptance-invalid-option'],
    expected=1, diagnostic="Unknown option(s) '[--acceptance-invalid-option]'",
    extra=('OPENMS_DATA_PATH=' + str(OUTPUT / 'invalid-core-data'),))
for case in (1, 2):
    image = OUTPUT / f'ImageCreator_{case}.bmp'
    options = ['-out_type', 'bmp', '-precursors', '-precursor_size', '3', '-precursor_color', 'green', '-log_intensity'] if case == 2 else []
    run(f'ImageCreator-{case}', [SDK / 'bin/ImageCreator', '-test', '-in', FIXTURES / f'imagecreator/ImageCreator_{case}_input.mzML',
        '-out', image, '-width', '20', '-height', '15', *options])
    if image.read_bytes() != (FIXTURES / f'imagecreator/ImageCreator_{case}_output.bmp').read_bytes():
        raise RuntimeError(f'ImageCreator {case} pixels differ')
run('pipeline', [SDK / 'bin/ExecutePipeline', '-test', '-in', FIXTURES / 'pipelines/ExecutePipeline_1.toppas',
    '-resource_file', FIXTURES / 'pipelines/ExecutePipeline_1.trf', '-out_dir', OUTPUT])
if not list(OUTPUT.rglob('*.tsv')) or not list(OUTPUT.rglob('*_mrgd.mzML')):
    raise RuntimeError('Pipeline reported success without its expected output artifacts')
print(f'{len(records)} isolated desktop runtime checks passed; ImageCreator outputs exactly match both fixtures.')
