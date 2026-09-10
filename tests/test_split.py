import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile
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


class ArtifactValidation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.files = self.root/'artifacts'; self.files.mkdir()
        self.file = self.files/'runtime.tar'; self.file.write_bytes(b'product')
        self.lock = {'schema_version':1,'core_source_revision':'a'*40,'artifacts':[{'path':self.file.name,'kind':'runtime','sha256':hashlib.sha256(b'product').hexdigest()}]}
        self.path = self.root/'lock.json'
    def tearDown(self):self.temp.cleanup()
    def verify(self):
        self.path.write_text(json.dumps(self.lock)); return artifacts.verified_artifacts(self.path,self.files)
    def test_correct_digest(self):self.assertEqual(len(self.verify()[1]),1)
    def test_changed_binary_rejected(self):
        self.file.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'mismatch'):self.verify()
    def test_placeholder_pin_rejected(self):
        self.lock['core_source_revision']='REPLACE_ME'
        with self.assertRaisesRegex(ValueError,'source commit'):self.verify()
    def test_extra_wheel_rejected(self):
        (self.files/'unapproved.whl').write_bytes(b'x')
        with self.assertRaisesRegex(ValueError,'Unlisted'):self.verify()
    def test_duplicate_artifact_rejected(self):
        self.lock['artifacts']*=2
        with self.assertRaisesRegex(ValueError,'unique'):self.verify()
    def test_parent_traversal_rejected_before_extraction(self):
        path=self.root/'unsafe.tar'
        with tarfile.open(path,'w') as archive:
            member=tarfile.TarInfo('../escape');member.size=3
            archive.addfile(member,io.BytesIO(b'bad'))
        with self.assertRaisesRegex(ValueError,'Unsafe'):artifacts.extract_runtime(path,self.root/'output')
        self.assertFalse((self.root/'escape').exists())
    def test_external_symlink_rejected(self):
        path=self.root/'unsafe.tar'
        with tarfile.open(path,'w') as archive:
            member=tarfile.TarInfo('escape');member.type=tarfile.SYMTYPE;member.linkname='/outside'
            archive.addfile(member)
        with self.assertRaises(tarfile.FilterError):artifacts.extract_runtime(path,self.root/'output')


if __name__ == '__main__':unittest.main()
