#!/usr/bin/env python3
"""Keep standalone consumer helpers identical to the parent-owned source."""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COPIES = {
    'OpenMS4Dependencies.cmake': ('cli', 'test-data', 'topp', 'openswath', 'flash', 'desktop', 'pyopenms', 'nuxl', 'prose', 'nase', 'comet', 'mascot', 'database-suitability', 'proteomics-lfq', 'parquet-diff', 'flashtnt'),
    'OpenMS4Tools.cmake': ('topp', 'openswath', 'flash', 'nuxl', 'prose', 'nase', 'comet', 'mascot', 'database-suitability', 'proteomics-lfq', 'parquet-diff', 'flashtnt'),
    'CheckToolMetadata.py': ('topp', 'openswath', 'flash', 'nuxl', 'prose', 'nase', 'comet', 'mascot', 'database-suitability', 'proteomics-lfq', 'parquet-diff', 'flashtnt'),
}


def sync(check=False):
    stale = []
    for name, packages in COPIES.items():
        content = (ROOT / 'cmake' / name).read_bytes()
        for package in packages:
            target = ROOT / 'packages' / package / 'cmake' / name
            if not target.exists() or target.read_bytes() != content:
                stale.append(str(target.relative_to(ROOT)))
                if not check:
                    target.write_bytes(content)
    return stale


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    stale = sync(args.check)
    if args.check and stale:
        parser.exit(1, 'Out-of-date generated helpers: ' + ', '.join(stale) + '\n')
