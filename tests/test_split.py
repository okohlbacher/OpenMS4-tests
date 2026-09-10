import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ROOT / 'packages'
SPEC = importlib.util.spec_from_file_location('artifacts', ROOT / 'tools/verify_artifacts.py')
artifacts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(artifacts)


class SourceOwnership(unittest.TestCase):
    def test_all_tool_sources_owned_once(self):
        inventory = json.loads((ROOT/'docs/baseline-inventory.json').read_text())
        names = []
        for package in ('topp', 'openswath', 'flash'):
            entries = json.loads((PACKAGES/package/'tools.json').read_text())['tools']
            for entry in entries:
                name = entry['name']; names.append(name)
                self.assertTrue((PACKAGES/package/'src'/f'{name}.cpp').is_file(), name)
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(sorted(names), sorted(inventory['cli_tools']))

    def test_textually_included_tool_helpers_are_present(self):
        for source in (PACKAGES/'topp/src').glob('*.cpp'):
            for helper in re.findall(r'#include\s+"([^"]+\.cpp)"', source.read_text()):
                self.assertTrue((source.parent/helper).is_file(), (source, helper))

    def test_science_has_no_cli_headers(self):
        paths = [PACKAGES/'core/src/openms/source', PACKAGES/'core/src/openms/include']
        for root in paths:
            for source in root.rglob('*'):
                if source.suffix not in {'.h', '.cpp'}:continue
                for dependency in re.findall(r'#include\s*[<"]OpenMS/APPLICATIONS/([^>"]+)', source.read_text(errors='replace')):
                    self.assertEqual(dependency, 'ConsoleUtils.h', source)

    def test_vendored_bytes_unchanged(self):
        inventory = json.loads((ROOT/'docs/baseline-inventory.json').read_text())
        for entry in inventory['tracked_files']:
            path = entry['path']
            if not path.startswith(('src/openms/extern/', 'src/openms/thirdparty/')) or entry['type'] != 'blob':continue
            data = (PACKAGES/'core'/path).read_bytes()
            digest = hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()
            self.assertEqual(digest, entry['git_object'], path)

    def test_core_fixtures_do_not_escape_to_tools(self):
        for source in (PACKAGES/'core/src/tests/class_tests/openms/source').glob('*.cpp'):
            self.assertNotIn('../../../topp/', source.read_text(), source)

    def test_no_unpinned_core_source_fallbacks(self):
        for package in ('cli','flash','openswath','topp','pyopenms'):
            cmake = (PACKAGES/package/'CMakeLists.txt').read_text()
            self.assertIn('openms4_find_core(', cmake)
            self.assertNotRegex(cmake,r'add_subdirectory\([^\n]*openms(?:\)|/)')


def load_tests(loader, suite, pattern):
    # Exercise the implementation actually copied into the app image.
    path = PACKAGES / 'flashapp/tests/test_artifacts.py'
    spec = importlib.util.spec_from_file_location('app_artifact_tests', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    suite.addTests(loader.loadTestsFromModule(module))
    return suite


if __name__ == '__main__':unittest.main()
