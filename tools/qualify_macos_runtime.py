#!/usr/bin/env python3
"""Copy, repair and sandbox-qualify a macOS tool runtime from an installed SDK.

Requires delocate 0.13 and CMake/Ninja. Builds only a small installed-SDK consumer.
Never modifies the SDK, source packages or Homebrew dependency installations.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tarfile
import tempfile

REPO = Path(__file__).resolve().parents[1]
TOOL_PACKAGES = {'topp': 'OpenMSTOPP', 'openswath': 'OpenMSOpenSWATH', 'flash': 'OpenMSFLASH'}


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def clean_environment():
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith('DYLD_') and key not in
                   {'OPENMS_DATA_PATH', 'OPENMS_HOME_PATH', 'OPENMS_TOOL_PREFIX_PATH',
                    'TOOL_PREFIX_PATH', 'CMAKE_PREFIX_PATH'}}
    environment.update(PATH='/usr/bin:/bin', OMP_NUM_THREADS='2', OPENMS_DISABLE_UPDATE_CHECK='ON')
    return environment


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def run(command, log, *, cwd=None, env=None, timeout=120, expected=0):
    result = subprocess.run(list(map(str, command)), cwd=cwd, env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    Path(log).parent.mkdir(parents=True, exist_ok=True)
    Path(log).write_text(result.stdout)
    if result.returncode != expected:
        raise RuntimeError(f'{command[0]} returned {result.returncode}; expected {expected}; see {log}')
    return result.stdout


def inspect(path):
    linked = subprocess.check_output(['/usr/bin/otool', '-L', str(path)], text=True)
    commands = subprocess.check_output(['/usr/bin/otool', '-l', str(path)], text=True)
    rpaths = re.findall(r'cmd LC_RPATH\s+cmdsize \d+\s+path (.*?) \(offset', commands)
    min_os = re.findall(r'\bminos ([0-9.]+)', commands)
    architectures = subprocess.check_output(['/usr/bin/lipo', '-archs', str(path)], text=True).split()
    return {'sha256': digest(path), 'dependencies': linked, 'rpaths': rpaths,
            'minimum_macos': min_os, 'architectures': architectures}


def verify_receipt(receipt_path, sdk, packages, required):
    """Check the trusted builder's clean source identities and exact installed bytes."""
    receipt = json.loads(Path(receipt_path).read_text())
    if receipt.get('schema_version') != 1 or receipt.get('sdk') != str(sdk):
        raise ValueError('Receipt schema or SDK prefix mismatch')
    recorded = receipt.get('packages', {})
    if set(recorded) != set(packages):
        raise ValueError('Receipt package set mismatch')
    files = {}
    for name, identity in packages.items():
        entry = recorded[name]
        if entry.get('source_dirty') is not False or any(entry.get(key) != identity[key]
                for key in ('source_revision', 'version')):
            raise ValueError(f'{name}: receipt does not match the selected clean source')
        for relative, info in entry.get('files', {}).items():
            path = sdk / relative
            if Path(relative).is_absolute() or '..' in Path(relative).parts or sdk not in path.resolve().parents:
                raise ValueError('Unsafe path in install receipt')
            if relative in files:
                raise ValueError('Duplicate file ownership in install receipt')
            files[relative] = info
            if not path.is_file() or digest(path) != info.get('sha256'):
                raise ValueError(f'Installed hash does not match receipt: {relative}')
            link = str(path.readlink()) if path.is_symlink() else None
            if info.get('symlink') != link:
                raise ValueError(f'Installed link does not match receipt: {relative}')
    if not {str(path.relative_to(sdk)) for path in required}.issubset(files):
        raise ValueError('Receipt is missing required runtime files')
    return files


def verify_signatures(native, evidence):
    def check(path):
        subprocess.run(['/usr/bin/codesign', '--verify', '--strict', str(path)], check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        return str(path)
    with ThreadPoolExecutor(max_workers=2) as pool:
        checked = list(pool.map(check, native))
    (evidence / 'signature-verification.json').write_text(json.dumps({'passed': True, 'files': checked}, indent=2) + '\n')
    return len(checked)


def archive_runtime(moved, archive, evidence, core, profile, environment):
    """Archive products without the test probe, then execute the extracted copies."""
    if archive.exists():
        raise ValueError('Refusing to overwrite a prior runtime archive')
    with tarfile.open(archive, 'w:gz') as target:
        for path in sorted(moved.iterdir()):
            target.add(path, arcname=path.name,
                       filter=lambda member: None if member.name == 'bin/sdk_runtime_identity' else member)
    # Use the same stdlib-only safe extraction routine deployed in the app.
    verifier = module('runtime_artifact_extractor', REPO / 'packages/flashapp/experimental/verify_artifacts.py')
    with tempfile.TemporaryDirectory(prefix='runtime archive ', dir=evidence) as temporary:
        extracted = Path(temporary)
        verifier.extract_runtime(archive, extracted)
        declared = json.loads((extracted / 'share/openms4/runtime-provenance.json').read_text())['executables']
        if set(declared) != {path.name for path in (extracted / 'bin').iterdir()}:
            raise ValueError('Archive executable set differs from its product manifest')
        # An independent installed-SDK consumer checks the actual extracted Core.
        # It is test instrumentation and is absent from the distributable archive.
        shutil.copy2(moved / 'bin/sdk_runtime_identity', extracted / 'bin/sdk_runtime_identity')
        archive_profile = evidence / 'archive-runtime.sb'
        archive_profile.write_text(profile.read_text() + '(deny file-read* (subpath ' + json.dumps(str(moved)) + '))\n')
        output = run(['/usr/bin/sandbox-exec', '-f', archive_profile, extracted / 'bin/sdk_runtime_identity', extracted],
                     evidence / 'archive-identity.log', cwd=evidence, env=environment)
        identity = json.loads(output.split('RUNTIME_IDENTITY_JSON\n', 1)[1])
        if identity['core'] != core or identity['registered_tools'] != len(declared):
            raise ValueError('Extracted runtime identity mismatch')
        run(['/usr/bin/sandbox-exec', '-f', archive_profile, extracted / 'bin/FileInfo', '--help'],
            evidence / 'archive-FileInfo-help.log', cwd=evidence, env=environment)
        (evidence / 'archive-verification.json').write_text(json.dumps({'passed': True, 'identity': identity,
            'product_executables': len(declared), 'test_probe_in_archive': False}, indent=2) + '\n')
    return {'path': str(archive), 'sha256': digest(archive), 'size': archive.stat().st_size}


def qualify(args):
    if platform.system() != 'Darwin' or platform.machine() != 'arm64':
        raise RuntimeError('This qualification is for macOS arm64 only')
    sdk, stage, moved, evidence = map(lambda path: Path(path).resolve(), (args.sdk, args.stage, args.moved, args.evidence))
    if stage == moved or any(path == sdk or sdk in path.parents or path == REPO or REPO in path.parents
                             for path in (stage, moved, evidence)):
        raise ValueError('Runtime and evidence must be distinct from the SDK and source tree')
    if not args.verify_only and (stage.exists() or moved.exists()):
        raise ValueError('Use new stage and moved paths; existing products are never overwritten')
    evidence.mkdir(parents=True, exist_ok=True)
    core = json.loads((sdk / 'lib/cmake/OpenMS/OpenMSBuildInfo.json').read_text())
    if core['source_dirty']:
        raise ValueError('A clean Core SDK is required')
    packages = {}
    for name, package in {'core': 'OpenMS', 'cli': 'OpenMSCLI', **TOOL_PACKAGES}.items():
        source = REPO / 'packages' / name
        sha = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
        dirty = subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True)
        if dirty:
            raise ValueError(f'Source package is dirty: {name}')
        packages[package] = {'source_revision': sha, 'version': '4.0.0' if name == 'core' else '1.0.0'}
    if packages['OpenMS']['source_revision'] != core['source_revision']:
        raise ValueError('Installed Core does not match the clean source pin')
    cli_config = (sdk / 'lib/cmake/OpenMSCLI/OpenMSCLIConfig.cmake').read_text()
    if f'set(OpenMSCLI_SOURCE_REVISION "{packages["OpenMSCLI"]["source_revision"]}")' not in cli_config:
        raise ValueError('Installed CLI does not match its clean source pin')

    tools = {}
    for package in TOOL_PACKAGES:
        manifest = sdk / 'share/openms4/tools' / f'{package}.tools.tsv'
        for line in manifest.read_text().splitlines():
            if not line or line.startswith('#'): continue
            name, category, version, relative = line.split('\t')
            if name in tools or relative != 'bin/' + name:
                raise ValueError('Duplicate or unexpected tool manifest path')
            tools[name] = {'category': category, 'version': version, 'path': relative, 'package': package}
    if len(tools) != 150:
        raise ValueError(f'Expected this pinned 150-tool build; found {len(tools)}')
    required = [sdk / info['path'] for info in tools.values()]
    for pattern in ('libOpenMS.dylib', 'libOpenSwathAlgo.dylib', 'libOpenMS_CLI*.dylib'):
        required += list(sdk.glob('lib/' + pattern))
    required += [sdk / f'share/openms4/tools/{package}.tools.tsv' for package in TOOL_PACKAGES]
    required += [sdk / 'lib/cmake/OpenMS/OpenMSBuildInfo.json', sdk / 'lib/cmake/OpenMSCLI/OpenMSCLIConfig.cmake']
    runtime_data = sdk / 'share/OpenMS/4.0.0'
    required += [path for path in runtime_data.rglob('*') if path.is_file() and not
                 {'test-data', 'examples', 'doc', 'docs'}.intersection(path.relative_to(runtime_data).parts)]
    verify_receipt(args.receipt, sdk, packages, required)
    shutil.copy2(args.receipt, evidence / 'native-install-receipt.json')
    if args.verify_only:
        copied = json.loads((evidence / 'copied-dependencies.json').read_text())
        licenses = [str(path.relative_to(moved)) for path in (moved / 'share/licenses').rglob('*') if path.is_file()]
        return validate_runtime(args, packages, tools, copied, licenses)
    (stage / 'bin').mkdir(parents=True)
    (stage / 'lib').mkdir()
    for name in tools:
        shutil.copy2(sdk / tools[name]['path'], stage / tools[name]['path'])
    for pattern in ('libOpenMS.dylib', 'libOpenSwathAlgo.dylib', 'libOpenMS_CLI*.dylib'):
        for library in sdk.glob('lib/' + pattern):
            target = stage / 'lib' / library.name
            if library.is_symlink(): target.symlink_to(os.readlink(library))
            else: shutil.copy2(library, target)
    data = stage / 'share/OpenMS/4.0.0'
    shutil.copytree(sdk / 'share/OpenMS/4.0.0', data,
                    ignore=shutil.ignore_patterns('test-data', 'examples', 'doc', 'docs'))
    (stage / 'share/openms4/tools').mkdir(parents=True)
    for package in TOOL_PACKAGES:
        shutil.copy2(sdk / f'share/openms4/tools/{package}.tools.tsv', stage / f'share/openms4/tools/{package}.tools.tsv')
    shutil.copy2(sdk / 'lib/cmake/OpenMS/OpenMSBuildInfo.json', stage / 'share/openms4/OpenMSBuildInfo.json')
    for name in ('LICENSE', 'License.txt'):
        if (REPO / 'packages/core' / name).is_file(): shutil.copy2(REPO / 'packages/core' / name, stage / name)

    # Preserve install evidence before relocation tooling rewrites anything.
    native = [*sorted((stage / 'bin').iterdir()), *[p for p in (stage / 'lib').iterdir() if not p.is_symlink()]]
    with ThreadPoolExecutor(max_workers=2) as pool:
        before = dict(zip([str(path.relative_to(stage)) for path in native], pool.map(inspect, native)))
    (evidence / 'before-repair.json').write_text(json.dumps(before, indent=2) + '\n')
    for name in tools:
        if '@loader_path/../lib' not in before['bin/' + name]['rpaths']:
            raise ValueError(f'{name}: incorrect installed product RPATH; refusing to hide it with repair')
    if '@loader_path/' not in before['lib/libOpenMS_CLI.1.0.0.dylib']['rpaths']:
        raise ValueError('CLI install RPATH is incorrect before repair')

    # Compile one consumer against imported installed Core/CLI targets, never source targets.
    probe_source = evidence / 'probe-source'; probe_source.mkdir()
    shutil.copy2(REPO / 'tools/runtime_sdk_probe.cpp', probe_source / 'probe.cpp')
    (probe_source / 'CMakeLists.txt').write_text('''cmake_minimum_required(VERSION 3.24)
project(RuntimeSDKProbe LANGUAGES CXX)
find_package(OpenMS 4.0.0 EXACT CONFIG REQUIRED)
find_package(OpenMSCLI 1.0.0 EXACT CONFIG REQUIRED)
add_executable(sdk_runtime_identity probe.cpp)
target_compile_features(sdk_runtime_identity PRIVATE cxx_std_23)
target_link_libraries(sdk_runtime_identity PRIVATE OpenMS::CLI OpenMS::Core ${CMAKE_DL_LIBS})
set_target_properties(sdk_runtime_identity PROPERTIES INSTALL_RPATH "@loader_path/../lib" INSTALL_RPATH_USE_LINK_PATH FALSE)
install(TARGETS sdk_runtime_identity RUNTIME DESTINATION bin)
''')
    probe_build = evidence / 'probe-build'
    configure = ['cmake', '-S', probe_source, '-B', probe_build, '-G', 'Ninja',
                 f'-DCMAKE_BUILD_TYPE={core["build_type"]}', f'-DCMAKE_PREFIX_PATH={sdk};/opt/homebrew;/opt/homebrew/opt/libomp',
                 '-DCURL_ROOT=/opt/homebrew/opt/curl', '-DCMAKE_FIND_FRAMEWORK=LAST', f'-DCMAKE_INSTALL_PREFIX={stage}']
    run(configure, evidence / 'probe-configure.log', timeout=180)
    run(['cmake', '--build', probe_build, '--parallel', '2'], evidence / 'probe-build.log', timeout=180)
    run(['cmake', '--install', probe_build], evidence / 'probe-install.log')

    # The host re2 links old Abseil 2601; this fallback is for dependency copying only.
    from delocate.delocating import delocate_path
    os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = str(Path(args.abseil_fallback).resolve())
    try:
        copied = delocate_path(str(stage), str(stage / 'lib'), sanitize_rpaths=True,
                              lib_filt_func=lambda name: name.endswith(('.dylib', '.so')) or str(name).startswith(str(stage / 'bin') + '/'))
    finally:
        os.environ.pop('DYLD_FALLBACK_LIBRARY_PATH', None)
    (evidence / 'copied-dependencies.json').write_text(json.dumps(copied, indent=2) + '\n')
    # Library IDs are not dependency edges; delocate_path does not rewrite them.
    from delocate.tools import set_install_id
    for library in sorted((stage / 'lib').glob('*.dylib')):
        if not library.is_symlink():
            set_install_id(str(library), '@rpath/' + library.name)
    # Preserve available license files from each copied Homebrew formula prefix.
    license_files = []
    formulas = {Path(*Path(dependency).resolve().parts[:6]) for dependency in copied
                if str(Path(dependency).resolve()).startswith('/opt/homebrew/Cellar/')}
    for formula in sorted(formulas):
        for file in formula.rglob('*'):
            if file.is_file() and re.search(r'(^|[/._-])(licen[cs]e|copying|notice)([/._-]|$)', str(file.relative_to(formula)), re.I):
                target = stage / 'share/licenses' / formula.parent.name / formula.name / file.relative_to(formula)
                target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(file, target)
                license_files.append(str(target.relative_to(stage)))
    stage.rename(moved)
    return validate_runtime(args, packages, tools, copied, license_files)


def validate_runtime(args, packages, tools, copied, license_files):
    sdk, stage, moved, evidence = map(lambda path: Path(path).resolve(), (args.sdk, args.stage, args.moved, args.evidence))
    core = json.loads((sdk / 'lib/cmake/OpenMS/OpenMSBuildInfo.json').read_text())
    probe_build = evidence / 'probe-build'
    receipt = json.loads(Path(args.receipt).read_text())
    recorded = {path: info for package in receipt['packages'].values() for path, info in package['files'].items()}
    before = json.loads((evidence / 'before-repair.json').read_text())
    if any(recorded[path]['sha256'] != info['sha256'] for path, info in before.items()):
        raise ValueError('Pre-repair binary hashes do not match the fresh install receipt')
    for path, info in recorded.items():
        if path.startswith(('bin/', 'lib/lib')) or path == 'lib/cmake/OpenMSCLI/OpenMSCLIConfig.cmake':
            continue
        relative = 'share/openms4/OpenMSBuildInfo.json' if path == 'lib/cmake/OpenMS/OpenMSBuildInfo.json' else path
        if digest(moved / relative) != info['sha256']:
            raise ValueError(f'Copied data or metadata does not match receipt: {relative}')
    native = sorted([p for p in (moved / 'bin').iterdir()] + [p for p in (moved / 'lib').iterdir() if not p.is_symlink()])
    if args.verify_only:
        previous = json.loads((evidence / 'after-repair.json').read_text())
        if set(previous) != {str(path.relative_to(moved)) for path in native} or any(
                digest(moved / path) != info['sha256'] for path, info in previous.items()):
            raise ValueError('The previously repaired runtime has changed')
    with ThreadPoolExecutor(max_workers=2) as pool:
        after = dict(zip([str(path.relative_to(moved)) for path in native], pool.map(inspect, native)))
    for name, info in after.items():
        if 'arm64' not in info['architectures']:
            raise ValueError(f'No arm64 slice in {name}')
        if any('/opt/homebrew' in line or str(sdk) in line or str(stage) in line for line in info['dependencies'].splitlines()[1:]):
            raise ValueError(f'Unrepaired dependency in {name}')
        if any(path.startswith('/') for path in info['rpaths']):
            raise ValueError(f'Absolute RPATH remains in {name}')
    (evidence / 'after-repair.json').write_text(json.dumps(after, indent=2) + '\n')
    signature_checks = verify_signatures(native, evidence)

    denied = {str(REPO), str(sdk), '/opt/homebrew', '/usr/local/opt'}
    workspace = REPO.parent
    for path in workspace.iterdir():
        if path.is_dir() and ('build' in path.name or path.name in {'implementation', 'core-sdk', 'installed-core-implementation'}):
            if evidence != path and evidence not in path.parents: denied.add(str(path))
    denied.add(str(probe_build))
    profile = evidence / 'runtime.sb'
    profile.write_text('(version 1)\n(allow default)\n(deny network*)\n' + '\n'.join(
        '(deny file-read* (subpath ' + json.dumps(path) + '))' for path in sorted(denied)) + '\n')
    environment = clean_environment()
    def isolated(name, arguments, expected=0, timeout=120):
        return run(['/usr/bin/sandbox-exec', '-f', profile, moved / 'bin' / name, *arguments],
                   evidence / 'logs' / (name + '-' + hashlib.sha256(str(arguments).encode()).hexdigest()[:10] + '.log'),
                   cwd=evidence, env=environment, expected=expected, timeout=timeout)
    for index, denied_file in enumerate([sdk / 'lib/libOpenMS.dylib', REPO / 'packages/core/CMakeLists.txt', Path('/opt/homebrew/opt/re2/lib/libre2.dylib')]):
        run(['/usr/bin/sandbox-exec', '-f', profile, '/bin/cat', denied_file], evidence / f'denial-control-{index}.log',
            env=environment, expected=1)
    identity_log = isolated('sdk_runtime_identity', [moved])
    identity = json.loads(identity_log.split('RUNTIME_IDENTITY_JSON\n', 1)[1])
    if identity['core'] != core or identity['registered_tools'] != len(tools):
        raise ValueError('Loaded Core identity or installed tool registry mismatch')
    (evidence / 'runtime-identity.json').write_text(json.dumps(identity, indent=2) + '\n')
    with ThreadPoolExecutor(max_workers=2) as pool:
        help_results = list(pool.map(lambda name: (name, isolated(name, ['--help'], timeout=30)), sorted(tools)))
    for name, output in help_results:
        if name not in output: raise ValueError(f'{name}: unexpected help output')
    metadata = module('runtime_metadata', REPO / 'cmake/CheckToolMetadata.py')
    metadata_dir = evidence / 'metadata'; metadata_dir.mkdir(exist_ok=True)
    for name in ('FileInfo', 'PeakPickerHiRes', 'FLASHDeconv', 'DecoyDatabase'):
        for kind in ('ini', 'ctd'):
            output = metadata_dir / f'{name}.{kind}'
            isolated(name, ['-test', '-write_' + kind, output if kind == 'ini' else metadata_dir])
            metadata.validate(output, name, tools[name]['version'], tools[name]['category'], kind)

    inputs = evidence / 'inputs'; inputs.mkdir(exist_ok=True)
    data_source = sdk / 'share/openms4-test-data/1.0.0/topp'
    for name in ('FileInfo_1_input.dta', 'PeakPickerHiRes_input.mzML', 'PeakPickerHiRes_parameters.ini',
                 'PeakPickerHiRes_output.mzML', 'DecoyDatabase_1.fasta', 'DecoyDatabase_1_out.fasta',
                 'FLASHDeconv_sample_input.mzML', 'FuzzyDiff.ini'):
        shutil.copy2(data_source / name, inputs / name)
    shutil.copy2(REPO / 'packages/flash/tests/data/FLASHDeconv_sample_pre_refactor.tsv', inputs / 'FLASHDeconv_reference.tsv')
    output = evidence / 'processing'; output.mkdir(exist_ok=True)
    isolated('FileInfo', ['-test', '-in', inputs / 'FileInfo_1_input.dta'])
    isolated('PeakPickerHiRes', ['-test', '-threads', '2', '-ini', inputs / 'PeakPickerHiRes_parameters.ini',
                               '-in', inputs / 'PeakPickerHiRes_input.mzML', '-out', output / 'picked.mzML'])
    isolated('FuzzyDiff', ['-test', '-ini', inputs / 'FuzzyDiff.ini', '-whitelist', 'offset', 'indexListOffset',
                           '-in1', output / 'picked.mzML', '-in2', inputs / 'PeakPickerHiRes_output.mzML'])
    isolated('DecoyDatabase', ['-test', '-threads', '2', '-in', inputs / 'DecoyDatabase_1.fasta',
                              '-out', output / 'decoy.fasta', '-only_decoy'])
    isolated('FuzzyDiff', ['-test', '-in1', output / 'decoy.fasta', '-in2', inputs / 'DecoyDatabase_1_out.fasta'])
    isolated('FLASHDeconv', ['-test', '-threads', '2', '-in', inputs / 'FLASHDeconv_sample_input.mzML',
                            '-out', output / 'flash.tsv'])
    module('runtime_flash_compare', REPO / 'packages/flash/tests/compare_features.py').compare(
        output / 'flash.tsv', inputs / 'FLASHDeconv_reference.tsv')
    (output / 'different.txt').write_text('meaningfully different\n')
    # Demonstrate FuzzyDiff detects a real mismatch, rather than only self-comparison.
    mismatch = subprocess.run(['/usr/bin/sandbox-exec', '-f', str(profile), str(moved / 'bin/FuzzyDiff'),
                               '-test', '-in1', str(output / 'decoy.fasta'), '-in2', str(output / 'different.txt')],
                              cwd=evidence, env=environment, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (evidence / 'fuzzy-negative.log').write_text(mismatch.stdout)
    if mismatch.returncode != 10: raise ValueError('FuzzyDiff did not report its expected comparison failure')

    provenance = {'schema_version': 1, 'core': core, 'packages': packages, 'executables': sorted(tools),
                  'external_tools': {}, 'build_receipt_sha256': digest(args.receipt),
                  'scope': 'Native tool runtime only; FLASHTnT and GUI are absent'}
    (moved / 'share/openms4/runtime-provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    shutil.copy2(args.receipt, moved / 'share/openms4/native-install-receipt.json')
    archive = archive_runtime(moved, moved.parent / 'openms4-tools-macos-arm64.tar.gz', evidence, core, profile, environment)
    summary = {'passed': True, 'platform': platform.platform(), 'core': core,
               'packages': packages, 'runtime_prefix': str(moved), 'tool_count': len(tools),
               'install_receipt_sha256': digest(args.receipt),
               'help_checks': len(help_results), 'metadata_checks': 8, 'signature_checks': signature_checks,
               'delocate_version': importlib.metadata.version('delocate'),
               'minimum_macos': max((version for info in after.values() for version in info['minimum_macos']),
                                    key=lambda value: tuple(map(int, value.split('.')))),
               'denied_read_paths': sorted(denied), 'environment_removed': ['DYLD_*', 'OPENMS_DATA_PATH', 'OPENMS_HOME_PATH', 'OPENMS_TOOL_PREFIX_PATH', 'TOOL_PREFIX_PATH'],
               'copied_libraries': len(copied), 'copied_license_files': sorted(set(license_files)),
               'input_sha256': {p.name: digest(p) for p in inputs.iterdir()},
               'output_sha256': {p.name: digest(p) for p in output.iterdir()},
               'archive': archive,
               'limits': ['Debug macOS arm64 runtime', 'No external FLASHTnT', 'No GUI or external search engines',
                          'No Linux/Windows/container execution', 'Ad-hoc dependency repair; no Developer ID signing or notarization',
                          'Source provenance is a trusted local incremental-builder receipt, not signed provenance or proof against a compromised build tree']}
    (evidence / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk', required=True)
    parser.add_argument('--receipt', required=True, help='Fresh record_native_install.py receipt')
    parser.add_argument('--verify-only', action='store_true', help='Recheck a hash-unchanged repaired runtime using its existing evidence')
    parser.add_argument('--stage', required=True)
    parser.add_argument('--moved', required=True)
    parser.add_argument('--evidence', required=True)
    parser.add_argument('--abseil-fallback', required=True)
    qualify(parser.parse_args())
