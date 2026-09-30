"""Reject valid XML carrying stale or missing product metadata."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    'tool_metadata', Path(__file__).resolve().parents[1] / 'cmake/CheckToolMetadata.py')
metadata = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metadata)


class ToolMetadataTests(unittest.TestCase):
    def check(self, xml, kind):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ('Probe.' + kind)
            path.write_text(xml)
            metadata.validate(path, 'Probe', '1.2.3', 'Experimental', kind)

    def test_ini_root_and_product_version(self):
        valid = '<PARAMETERS><NODE name="Probe"><ITEM name="version" value="1.2.3"/></NODE></PARAMETERS>'
        self.check(valid, 'ini')
        for invalid in (valid.replace('PARAMETERS', 'unrelated'),
                        valid.replace('1.2.3', '3.6.0'),
                        valid.replace('Probe', 'Other')):
            with self.subTest(xml=invalid), self.assertRaises(ValueError):
                self.check(invalid, 'ini')

    def test_ctd_checks_both_versions_and_category(self):
        valid = ('<tool name="Probe" version="1.2.3" category="Experimental">'
                 '<PARAMETERS><NODE name="Probe"><ITEM name="version" value="1.2.3"/>'
                 '</NODE></PARAMETERS></tool>')
        self.check(valid, 'ctd')
        for invalid in (valid.replace('version="1.2.3"', 'version="3.6.0"'),
                        valid.replace('value="1.2.3"', 'value="3.6.0"'),
                        valid.replace('category="Experimental"', 'category=""'),
                        valid.replace('category="Experimental"', ''),
                        valid.replace('name="Probe"', 'name="Other"', 1)):
            with self.subTest(xml=invalid), self.assertRaises(ValueError):
                self.check(invalid, 'ctd')


if __name__ == '__main__':
    unittest.main()
