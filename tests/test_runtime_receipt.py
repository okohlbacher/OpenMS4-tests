"""Isolated negative cases for the native trusted-builder receipt contract."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest

spec = importlib.util.spec_from_file_location('runtime_qualification',
    Path(__file__).resolve().parents[1] / 'tools/qualify_macos_runtime.py')
qualification = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qualification)


class InstallReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.sdk = self.root / 'sdk'
        (self.sdk / 'bin').mkdir(parents=True)
        self.tool = self.sdk / 'bin/Tool'
        self.tool.write_bytes(b'the installed binary')
        self.packages = {'OpenMSTOPP': {'source_revision': 'a' * 40, 'version': '1.0.0'}}
        self.receipt = {'schema_version': 1, 'sdk': str(self.sdk), 'packages': {
            'OpenMSTOPP': {**self.packages['OpenMSTOPP'], 'source_dirty': False,
                'files': {'bin/Tool': {'sha256': qualification.digest(self.tool), 'symlink': None}}}}}
        self.path = self.root / 'receipt.json'

    def check(self, receipt=None, packages=None, required=None):
        self.path.write_text(json.dumps(self.receipt if receipt is None else receipt))
        return qualification.verify_receipt(self.path, self.sdk,
            self.packages if packages is None else packages, [self.tool] if required is None else required)

    def test_exact_installed_bytes_and_source_match(self):
        self.assertIn('bin/Tool', self.check())

    def test_command_line_requires_receipt_before_any_work(self):
        script = Path(__file__).resolve().parents[1] / 'tools/qualify_macos_runtime.py'
        result = subprocess.run([sys.executable, str(script), '--sdk', str(self.sdk),
            '--stage', str(self.root / 'stage'), '--moved', str(self.root / 'moved'),
            '--evidence', str(self.root / 'evidence'), '--abseil-fallback', str(self.root)],
            text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('--receipt', result.stderr)
        self.assertFalse((self.root / 'stage').exists())

    def test_missing_receipt(self):
        with self.assertRaises(FileNotFoundError):
            qualification.verify_receipt(self.path, self.sdk, self.packages, [self.tool])

    def test_wrong_hash(self):
        self.receipt['packages']['OpenMSTOPP']['files']['bin/Tool']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'hash'):
            self.check()

    def test_stale_binary_cannot_receive_new_clean_source_pin(self):
        later_clean_head = {'OpenMSTOPP': {'source_revision': 'b' * 40, 'version': '1.0.0'}}
        with self.assertRaisesRegex(ValueError, 'clean source'):
            self.check(packages=later_clean_head)

    def test_replaced_installed_binary(self):
        self.tool.write_bytes(b'other build')
        with self.assertRaisesRegex(ValueError, 'hash'):
            self.check()

    def test_missing_runtime_file(self):
        self.receipt['packages']['OpenMSTOPP']['files'].clear()
        with self.assertRaisesRegex(ValueError, 'missing required'):
            self.check()

    def test_dirty_source_and_version(self):
        for field, value in [('source_dirty', True), ('version', '2.0.0')]:
            with self.subTest(field=field):
                receipt = copy.deepcopy(self.receipt)
                receipt['packages']['OpenMSTOPP'][field] = value
                with self.assertRaisesRegex(ValueError, 'clean source'):
                    self.check(receipt)

    def test_wrong_schema_prefix_or_package(self):
        for field, value in [('schema_version', 2), ('sdk', str(self.root)), ('packages', {})]:
            with self.subTest(field=field):
                receipt = copy.deepcopy(self.receipt); receipt[field] = value
                with self.assertRaises(ValueError):
                    self.check(receipt)

    def test_path_traversal(self):
        info = self.receipt['packages']['OpenMSTOPP']['files'].pop('bin/Tool')
        self.receipt['packages']['OpenMSTOPP']['files']['../outside'] = info
        with self.assertRaisesRegex(ValueError, 'Unsafe path'):
            self.check()

    def test_symlink_target_is_part_of_receipt(self):
        alternate = self.sdk / 'bin/Other'; alternate.write_bytes(self.tool.read_bytes())
        link = self.sdk / 'bin/Alias'; link.symlink_to('Tool')
        self.receipt['packages']['OpenMSTOPP']['files']['bin/Alias'] = {
            'sha256': qualification.digest(link), 'symlink': 'Tool'}
        self.check(required=[self.tool, link])
        link.unlink(); link.symlink_to('Other')
        with self.assertRaisesRegex(ValueError, 'link'):
            self.check(required=[self.tool, link])

    def test_link_cannot_escape_sdk(self):
        outside = self.root / 'outside'; outside.write_bytes(self.tool.read_bytes())
        self.tool.unlink(); self.tool.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'Unsafe path'):
            self.check()

    def test_duplicate_file_ownership(self):
        receipt = copy.deepcopy(self.receipt)
        receipt['packages']['OpenMSFLASH'] = copy.deepcopy(receipt['packages']['OpenMSTOPP'])
        packages = {**self.packages, 'OpenMSFLASH': self.packages['OpenMSTOPP']}
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.check(receipt, packages)


if __name__ == '__main__':
    unittest.main()
