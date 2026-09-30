#!/usr/bin/env python3
"""Run a tool's metadata writer and validate the emitted XML and product identity."""
import argparse
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET


def validate(path, name, version, category, kind):
    root = ET.parse(path).getroot()
    if kind == 'ctd':
        if root.tag != 'tool' or root.get('name') != name or root.get('version') != version:
            raise ValueError(f'Wrong CTD product identity: {path}')
        if root.get('category') != category:
            raise ValueError(f'Wrong emitted CTD category: {path}')
    elif root.tag != 'PARAMETERS':
        raise ValueError(f'Wrong INI XML root: {path}')
    node = root.find(f".//NODE[@name='{name}']/ITEM[@name='version']")
    if node is None or node.get('value') != version:
        raise ValueError(f'Missing or incorrect parameter-file product version: {path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tool')
    parser.add_argument('name')
    parser.add_argument('version')
    parser.add_argument('category')
    parser.add_argument('kind', choices=('ini', 'ctd'))
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    destination = args.output if args.kind == 'ini' else args.output.parent
    args.output.unlink(missing_ok=True)
    subprocess.run([args.tool, '-test', '-write_' + args.kind, str(destination)], check=True)
    validate(args.output, args.name, args.version, args.category, args.kind)
