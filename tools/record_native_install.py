#!/usr/bin/env python3
"""Refresh guarded native builds and record the installed files for runtime assembly.

This is a trusted-builder receipt, not cryptographic proof of arbitrary object files.
Existing configured Ninja builds are required. Native compilation uses at most two jobs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from datetime import datetime, timezone

PACKAGES = {'core': 'OpenMS', 'cli': 'OpenMSCLI', 'topp': 'OpenMSTOPP',
            'openswath': 'OpenMSOpenSWATH', 'flash': 'OpenMSFLASH'}
REPO = Path(__file__).resolve().parents[1]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def clean_head(source):
    sha = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    if subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True):
        raise ValueError(f'Dirty source: {source}')
    return sha


def installed_files(sdk, name):
    if name == 'core':
        paths = list(sdk.glob('lib/libOpenMS.dylib')) + list(sdk.glob('lib/libOpenSwathAlgo.dylib'))
        paths += [sdk / 'lib/cmake/OpenMS/OpenMSBuildInfo.json']
        data = sdk / 'share/OpenMS/4.0.0'
        paths += [path for path in data.rglob('*') if path.is_file() and not
                  {'test-data', 'examples', 'doc', 'docs'}.intersection(path.relative_to(data).parts)]
    elif name == 'cli':
        paths = list(sdk.glob('lib/libOpenMS_CLI*.dylib'))
        paths += [sdk / 'lib/cmake/OpenMSCLI/OpenMSCLIConfig.cmake']
    else:
        manifest = sdk / f'share/openms4/tools/{name}.tools.tsv'
        paths = [manifest]
        for line in manifest.read_text().splitlines():
            if line and not line.startswith('#'):
                relative = line.split('\t')[3]
                if not re.fullmatch(r'bin/[A-Za-z0-9_]+', relative):
                    raise ValueError(f'Unexpected executable path: {relative}')
                paths.append(sdk / relative)
    return paths


def record(args):
    sdk, build_root, evidence = (Path(value).resolve() for value in (args.sdk, args.build_root, args.evidence))
    evidence.mkdir(parents=True, exist_ok=True)
    receipt = {'schema_version': 1, 'created_utc': datetime.now(timezone.utc).isoformat(),
               'sdk': str(sdk), 'trust': 'Local guarded incremental build and install; trusted compiler/build tree',
               'packages': {}}
    for name, package in PACKAGES.items():
        source = REPO / 'packages' / name
        build = build_root / (name + '-build')
        sha = clean_head(source)
        cache = (build / 'CMakeCache.txt').read_text()
        fields = {}
        for line in cache.splitlines():
            match = re.match(r'([^#/:][^:=]*):[^=]*=(.*)', line)
            if match: fields[match[1]] = match[2]
        clean_option = 'OPENMS_REQUIRE_CLEAN_SOURCE' if name == 'core' else 'OPENMS4_REQUIRE_CLEAN_SOURCE'
        if fields.get('CMAKE_HOME_DIRECTORY') != str(source) or fields.get('CMAKE_INSTALL_PREFIX') != str(sdk) or fields.get(clean_option) != 'ON':
            raise ValueError(f'{name}: wrong source, install prefix, or clean-source guard')
        expected = 'OPENMS_EXPECTED_REVISION' if name == 'core' else 'OPENMS4_EXPECTED_REVISION'
        guards = [line.strip() for line in (build / 'build.ninja').read_text().splitlines()
                  if 'COMMAND =' in line and f'-D{expected}={sha}' in line and f'-D{clean_option}=ON' in line]
        if len(guards) != 1:
            raise ValueError(f'{name}: configured source guard does not match clean HEAD')
        commands = [['cmake', '--build', str(build), '--parallel', '2'], ['cmake', '--install', str(build)]]
        for index, command in enumerate(commands):
            with (evidence / f'{name}-{index}.log').open('w') as log:
                subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=3600)
            if clean_head(source) != sha:
                raise ValueError(f'{name}: source changed during build/install')
        installed = set((build / 'install_manifest.txt').read_text().splitlines())
        files = {}
        for path in installed_files(sdk, name):
            if str(path) not in installed:
                raise ValueError(f'{path} was not in this fresh install manifest')
            if sdk not in path.resolve().parents:
                raise ValueError(f'Installed link escapes SDK: {path}')
            files[str(path.relative_to(sdk))] = {'sha256': digest(path),
                'symlink': str(path.readlink()) if path.is_symlink() else None}
        receipt['packages'][package] = {'source_revision': sha, 'source_dirty': False,
            'version': '4.0.0' if name == 'core' else '1.0.0', 'source': str(source), 'build': str(build),
            'configure_cache_sha256': digest(build / 'CMakeCache.txt'),
            'ninja_sha256': digest(build / 'build.ninja'), 'guard_command': guards[0], 'commands': commands,
            'install_manifest_sha256': digest(build / 'install_manifest.txt'), 'files': files}
    for name, package in PACKAGES.items():
        if clean_head(REPO / 'packages' / name) != receipt['packages'][package]['source_revision']:
            raise ValueError(f'{name}: source changed before receipt completion')
    output = Path(args.output).resolve()
    if output.exists(): raise ValueError('Refusing to overwrite an earlier receipt')
    output.write_text(json.dumps(receipt, indent=2) + '\n')
    print(f'Recorded {sum(len(p["files"]) for p in receipt["packages"].values())} installed files in {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk', required=True)
    parser.add_argument('--build-root', required=True)
    parser.add_argument('--evidence', required=True)
    parser.add_argument('--output', required=True)
    record(parser.parse_args())
