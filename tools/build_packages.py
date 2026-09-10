#!/usr/bin/env python3
"""Build and test the split native packages against an installed, pinned Core SDK.

Provision compatible third-party dependencies and CC/CXX first. Core is copied
into a new combined deployment prefix; its original installation is untouched.
FLASHApp's Python/container acceptance is a separate step.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from graphlib import TopologicalSorter
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]


def native_graph(packages):
    by_repo = {entry['repository'].removesuffix('.git').lower(): name
               for name, entry in packages.items()}
    graph = {}
    for name, entry in packages.items():
        if name in ('core', 'flashapp'):
            continue
        lock = json.loads((ROOT / entry['path'] / 'dependencies.lock.json').read_text())
        graph[name] = {by_repo[dep['repository'].removesuffix('.git').lower()]
                       for dep in lock['dependencies'].values()} - {'core'}
    return graph


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--core-prefix', required=True, type=Path)
    parser.add_argument('--dependencies', required=True, type=Path)
    parser.add_argument('--work-dir', required=True, type=Path)
    parser.add_argument('--jobs', type=int, default=os.cpu_count() or 2)
    parser.add_argument('--workers', type=int, default=4)
    args = parser.parse_args()
    work, core, deps = (p.resolve() for p in (args.work_dir, args.core_prefix, args.dependencies))
    if min(args.jobs, args.workers) < 1 or (work.exists() and any(work.iterdir())):
        parser.error('job counts must be positive and the work directory must be empty')
    if any(work == p or work in p.parents or p in work.parents for p in (ROOT, core, deps)):
        parser.error('work directory must be separate from sources and installed dependencies')
    packages = json.loads((ROOT / 'packages.lock.json').read_text())['packages']
    graph = native_graph(packages)
    for name in ('core', *graph):
        source = ROOT / packages[name]['path']
        head = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
        dirty = subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True).strip()
        if dirty or head != packages[name]['source_revision']:
            parser.error(f'{name}: source must be clean and match packages.lock.json')
    info = json.loads((core / 'lib/cmake/OpenMS/OpenMSBuildInfo.json').read_text())
    if info['source_dirty'] or info['source_revision'] != packages['core']['source_revision']:
        parser.error('installed Core does not match the clean pinned source')
    config = info['build_type']
    sdk, results = work / 'sdk', work / 'results'
    results.mkdir(parents=True)
    shutil.copytree(core, sdk, symlinks=True)
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENMS_RUN_SLOW_TESTS='1',
               QT_QPA_PLATFORM='minimal', PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1')
    for name in ('OPENMS_DATA_PATH', 'PYTHONPATH', 'OPENMS_CONTRIB_LIBS'):
        env.pop(name, None)
    env['PATH'] = os.pathsep.join([str(deps / 'bin'), str(sdk / 'bin'), env['PATH']])
    if sys.platform == 'linux':
        env['LD_LIBRARY_PATH'] = str(deps / 'lib')
    elif sys.platform == 'darwin':
        env['DYLD_FALLBACK_LIBRARY_PATH'] = str(deps / 'lib')
    elif sys.platform == 'win32':
        env['PATH'] = str(deps / 'Library/bin') + os.pathsep + env['PATH']
    cmake, ctest = (shutil.which(name, path=env['PATH']) for name in ('cmake', 'ctest'))
    dependency_prefix = deps / 'Library' if sys.platform == 'win32' else deps
    common = [f'-DCMAKE_BUILD_TYPE={config}', f'-DCMAKE_INSTALL_PREFIX={sdk}',
              f'-DCMAKE_PREFIX_PATH={sdk};{dependency_prefix}', '-DOPENMS4_REQUIRE_CLEAN_SOURCE=ON']
    if sys.platform == 'win32':
        common += ['-G', 'Visual Studio 17 2022', '-A', 'x64',
                   f'-DCMAKE_MSVC_RUNTIME_LIBRARY={info["msvc_runtime_library"]}']
    else:
        common += ['-G', 'Ninja']
    install_lock = threading.Lock()

    def run(label, command, extra_env=None):
        start = time.monotonic()
        print('START', label, flush=True)
        log = results / f'{label}.log'
        with log.open('w') as output:
            result = subprocess.run(command, cwd=work, env={**env, **(extra_env or {})},
                                    stdout=output, stderr=subprocess.STDOUT)
        receipt = dict(command=command, returncode=result.returncode,
                       elapsed_seconds=round(time.monotonic() - start, 3))
        (results / f'{label}.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print('END', label, receipt, flush=True)
        if result.returncode:
            print('\n'.join(log.read_text(errors='replace').splitlines()[-40:]), flush=True)
            raise RuntimeError(f'{label} failed: {log}')

    def build_package(name, jobs):
        source, build = ROOT / packages[name]['path'], work / 'build' / name
        options = ['-DBUILD_TESTING=ON']
        if name in ('topp', 'openswath', 'flash', 'nuxl', 'nase'):
            options += ['-DOPENMS4_REGRESSION_TESTS=ON']
        elif name == 'desktop':
            options += ['-DOPENMS_GUI_WEBENGINE=OFF', '-DOPENMS_DESKTOP_INTERACTIVE_TESTS=OFF',
                        '-DOPENMS_DESKTOP_PIPELINE_TESTS=ON']
        elif name == 'pyopenms':
            options += ['-DPYOPENMS_BUILD_TESTING=ON', '-DPYOPENMS_GENERATE_STUBS=ON',
                        f'-DPython_EXECUTABLE={sys.executable}']
            if sys.platform == 'win32':
                options += [f'-DPYOPENMS_DLL_PATH={dependency_prefix / "bin"}']
            else:
                origin = '@loader_path' if sys.platform == 'darwin' else '$ORIGIN'
                options += [f'-DCMAKE_INSTALL_RPATH={origin}/../lib']
        run(name + '-configure', [cmake, '-S', str(source), '-B', str(build), *common, *options])
        run(name + '-build', [cmake, '--build', str(build), '--config', config, '--parallel', str(jobs)])
        if name != 'test-data':
            run(name + '-tests', [ctest, '--test-dir', str(build), '-C', config,
                '--parallel', str(min(jobs, 32)), '--output-on-failure', '--no-tests=error',
                '--output-junit', str(results / f'{name}-tests.xml')],
                {'OMP_NUM_THREADS': str(min(jobs, 16))} if name == 'flash' else None)
        with install_lock:
            run(name + '-install', [cmake, '--install', str(build), '--config', config])

    sorter = TopologicalSorter(graph)
    sorter.prepare()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        while sorter.is_active():
            ready = sorter.get_ready()
            jobs = max(1, args.jobs // min(args.workers, len(ready)))
            futures = [pool.submit(build_package, name, jobs) for name in ready]
            for future in futures:
                future.result()
            sorter.done(*ready)
    # The installed fixture harness exercises numerical output across all products.
    names = []
    for manifest in sorted((sdk / 'share/openms4/tools').glob('*.tools.tsv')):
        if manifest.name in ('openms-viewers.tools.tsv', 'openms-workflows.tools.tsv'):
            continue
        names += [line.split('\t')[0] for line in manifest.read_text().splitlines()
                  if line and not line.startswith('#')]
    if not names or len(names) != len(set(names)):
        raise RuntimeError('missing or duplicate installed tool registrations')
    build = work / 'build' / 'regressions'
    run('regressions-configure', [cmake, '-S', str(sdk / 'share/openms4-test-data/1.0.0'),
        '-B', str(build), *common, '-DOPENMS4_REGRESSION_TESTS=ON',
        f'-DOPENMS4_TOOLS_BIN={sdk}/bin', '-DOPENMS4_TOOL_NAMES=' + ';'.join(sorted(names)),
        '-DWITH_GUI=OFF', '-DHAS_XSERVER=OFF'])
    run('regressions-tests', [ctest, '--test-dir', str(build), '-C', config,
        '--parallel', str(min(args.jobs, 128)), '--output-on-failure', '--no-tests=error',
        '--output-junit', str(results / 'regressions-tests.xml')])
    (results / 'packages.json').write_text(json.dumps(packages, indent=2) + '\n')
    print(f'Installed {len(names)} console tools and native packages in {sdk}', flush=True)


if __name__ == '__main__':
    main()
