"""Configure actual consumer CMake projects against an isolated mock SDK; do not compile."""
import json
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import unittest
from test_split import PACKAGES

class ConsumerConfigure(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.sdk=self.root/'sdk';self.sdk.mkdir()
        (self.sdk/'support.cpp').write_text('// configure-only fixture\n')
        self.config('OpenMS','4.0.0', '''set(OpenMS_SOURCE_REVISION "'''+ 'a'*40+'''")
set(OpenMS_SOURCE_DIRTY OFF)
set(OpenMS_VERSION 4.0.0)
set(OpenMS_WITH_OPENSWATH ON)
set(OpenMS_WITH_WNETALIGN OFF)
foreach(name Boost::regex Eigen3::Eigen)
  if(NOT TARGET ${name})
    add_library(${name} INTERFACE IMPORTED)
  endif()
endforeach()
set(OpenMS_TEST_SUPPORT_SOURCE "${CMAKE_CURRENT_LIST_DIR}/../../../support.cpp")
foreach(name Core OpenSwathAlgo Arrow TestFramework)
  if(NOT TARGET OpenMS::${name})
    add_library(OpenMS::${name} INTERFACE IMPORTED)
  endif()
endforeach()
''')
        self.config('OpenMSCLI','1.0.0','set(OpenMSCLI_SOURCE_DIRTY OFF)\nset(OpenMSCLI_SOURCE_REVISION "'+'b'*40+'")\nif(NOT TARGET OpenMS::CLI)\n add_library(OpenMS::CLI INTERFACE IMPORTED)\nendif()\n')
        self.config('Boost','1.90.0','if(NOT TARGET Boost::regex)\n add_library(Boost::regex INTERFACE IMPORTED)\nendif()\n')
        self.config('Eigen3','3.4.0','if(NOT TARGET Eigen3::Eigen)\n add_library(Eigen3::Eigen INTERFACE IMPORTED)\nendif()\n')
        self.lock=self.root/'lock.json'
        self.write_lock('a'*40)
    def tearDown(self):self.temp.cleanup()
    def write_lock(self,revision):
        self.lock.write_text(json.dumps({'dependencies':{'OpenMS':{'version':'4.0.0','source_revision':revision},'OpenMSCLI':{'version':'1.0.0','source_revision':'b'*40}}}))
    def config(self,name,version,body):
        p=self.sdk/'lib/cmake'/name;p.mkdir(parents=True)
        (p/f'{name}Config.cmake').write_text(body)
        (p/f'{name}ConfigVersion.cmake').write_text(f'set(PACKAGE_VERSION "{version}")\nif(PACKAGE_FIND_VERSION VERSION_EQUAL PACKAGE_VERSION)\nset(PACKAGE_VERSION_EXACT TRUE)\nendif()\nif(NOT PACKAGE_FIND_VERSION VERSION_GREATER PACKAGE_VERSION)\nset(PACKAGE_VERSION_COMPATIBLE TRUE)\nendif()\n')
    def configure(self,package,testing=False,extra=()):
        return subprocess.run(['cmake','-S',str(PACKAGES/package),'-B',str(self.root/'build'),f'-DCMAKE_PREFIX_PATH={self.sdk}',f'-DOPENMS4_DEPENDENCY_LOCK_FILE={self.lock}','-DOPENMS4_SOURCE_REVISION='+'c'*40,'-DOPENMS4_SOURCE_DIRTY=OFF','-DCMAKE_FIND_PACKAGE_PREFER_CONFIG=ON','-DCMAKE_INSTALL_BINDIR=custom-bin','-DBUILD_TESTING='+('ON' if testing else 'OFF'), *extra],text=True,capture_output=True)
    def check(self,package,testing=False):
        result=self.configure(package,testing);self.assertEqual(result.returncode,0,result.stdout+result.stderr)
    def test_cli_configuration(self):self.check('cli',True)
    def test_topp_configuration_and_manifest_paths(self):
        self.check('topp',True)
        self.assertIn('\tbin/FileInfo',(self.root/'build/share/openms4/tools/topp.tools.tsv').read_text())
        self.assertIn('\tcustom-bin/FileInfo',(self.root/'build/install-manifests/topp.tools.tsv').read_text())
        registered = subprocess.run(['ctest', '--test-dir', str(self.root/'build'),
                                     '--show-only=json-v1'], text=True, capture_output=True, check=True)
        names = [test['name'] for test in json.loads(registered.stdout)['tests']]
        metadata = json.loads((PACKAGES/'topp/tools.json').read_text())['tools']
        expected = {entry['name'] + '_write_' + kind for entry in metadata
                    if entry['name'] != 'OpenMSInfo' and not entry.get('requires_feature')
                    for kind in ('ini', 'ctd')}
        self.assertEqual(set(names), expected)

    def test_swath_configuration(self):self.check('openswath',True)
    def test_flash_configuration(self):self.check('flash',True)
    def test_wrong_core_pin_is_rejected(self):
        self.write_lock('d'*40);result=self.configure('flash')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('SDK revision mismatch',result.stdout+result.stderr)
    def test_short_pin_is_rejected(self):
        self.write_lock('a'*12);result=self.configure('flash')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('40-character',result.stdout+result.stderr)

    def metadata_fixture(self, change):
        source = self.root / 'mutated-topp'
        source.mkdir()
        shutil.copy2(PACKAGES/'topp/CMakeLists.txt', source/'CMakeLists.txt')
        for name in ('src', 'cmake', 'tests'):
            (source/name).symlink_to(PACKAGES/'topp'/name, target_is_directory=True)
        metadata = json.loads((PACKAGES/'topp/tools.json').read_text())
        change(metadata['tools'])
        (source/'tools.json').write_text(json.dumps(metadata))
        return source

    def test_missing_metadata_is_rejected(self):
        source = self.metadata_fixture(lambda tools: tools.pop(1))
        result = self.configure(source)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('missing metadata: AssayGeneratorMetabo', result.stdout+result.stderr)

    def test_duplicate_metadata_is_rejected(self):
        source = self.metadata_fixture(lambda tools: tools.append(tools[0]))
        result = self.configure(source)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Invalid or duplicate tool metadata', result.stdout+result.stderr)

    @unittest.skipIf(sys.platform == 'win32', 'Windows uses the colocated DLL policy')
    def test_install_rpath_keeps_relative_library_lookup(self):
        self.check('cli')
        script = (self.root/'build/cmake_install.cmake').read_text()
        if sys.platform == 'darwin':
            self.assertIn('@loader_path/', script)
        else:
            self.assertIn('$ORIGIN/', script)

    def test_clean_sdk_policy_rejects_missing_invalid_and_dirty_metadata(self):
        core = self.sdk / 'lib/cmake/OpenMS/OpenMSConfig.cmake'
        original = core.read_text()
        for value in (None, '', 'unknown', 'ON'):
            with self.subTest(value=value):
                replacement = '' if value is None else f'set(OpenMS_SOURCE_DIRTY "{value}")'
                core.write_text(original.replace('set(OpenMS_SOURCE_DIRTY OFF)', replacement))
                result = self.configure('flash', extra=('-DOPENMS4_REQUIRE_CLEAN_SOURCE=ON',))
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('SOURCE_DIRTY' if value != 'ON' else 'uncommitted sources', result.stdout + result.stderr)
        core.write_text(original)
        result = self.configure('flash', extra=('-DOPENMS4_REQUIRE_CLEAN_SOURCE=ON',))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_changed_lock_is_checked_by_an_existing_build(self):
        self.check('flash')
        self.write_lock('d' * 40)
        result = subprocess.run(['cmake', '--build', str(self.root / 'build'),
                                 '--target', 'OpenMSFLASH_source_identity'], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('SDK revision mismatch', result.stdout + result.stderr)

    def test_changed_tool_metadata_regenerates_manifest(self):
        source = self.metadata_fixture(lambda tools: None)
        result = self.configure(source)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        path = source / 'tools.json'
        data = json.loads(path.read_text())
        data['tools'][0]['category'] = 'ChangedCategory'
        path.write_text(json.dumps(data))
        result = subprocess.run(['cmake', '--build', str(self.root / 'build'),
                                 '--target', 'OpenMSTOPP_source_identity'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('ChangedCategory', (self.root / 'build/install-manifests/topp.tools.tsv').read_text())

    def test_compiler_free_data_discovery_enforces_clean_metadata(self):
        self.config('OpenMSData', '4.0.0', 'set(OpenMSData_SOURCE_REVISION "' + 'a' * 40 + '")\n')
        source = self.root / 'data-consumer'
        source.mkdir()
        (source / 'CMakeLists.txt').write_text(f'''cmake_minimum_required(VERSION 3.24)
project(DataConsumer LANGUAGES NONE)
include("{PACKAGES.parent}/cmake/OpenMS4Dependencies.cmake")
openms4_find_core_data()
''')
        result = self.configure(source, extra=('-DOPENMS4_REQUIRE_CLEAN_SOURCE=ON',))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('OpenMSData_SOURCE_DIRTY', result.stdout + result.stderr)
        config = self.sdk / 'lib/cmake/OpenMSData/OpenMSDataConfig.cmake'
        config.write_text(config.read_text() + 'set(OpenMSData_SOURCE_DIRTY OFF)\n')
        result = self.configure(source, extra=('-DOPENMS4_REQUIRE_CLEAN_SOURCE=ON',))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_generated_helpers_match_canonical_source(self):
        result = subprocess.run([sys.executable, str(PACKAGES.parent/'tools/sync_build_helpers.py'), '--check'],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)

class ConsumerSourceIdentity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='consumer-identity-')
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.helper = PACKAGES.parent / 'cmake/OpenMS4Dependencies.cmake'

    def tearDown(self):
        self.temp.cleanup()

    def run_command(self, arguments, success=True):
        result = subprocess.run(list(map(str, arguments)), cwd=self.source, capture_output=True, text=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def test_archives_require_normalized_explicit_dirty_assertions(self):
        script = self.root / 'archive.cmake'
        script.write_text(f'''set(PROJECT_SOURCE_DIR "{self.source}")
include("{self.helper}")
openms4_source_revision(revision dirty)
file(WRITE "{self.root}/dirty.txt" "${{dirty}}")
''')
        command = ['cmake', '-DOPENMS4_SOURCE_REVISION=' + 'a' * 40]
        for value in ('', 'unknown', 'NOTFOUND'):
            with self.subTest(value=value):
                result = self.run_command([*command, '-DOPENMS4_SOURCE_DIRTY=' + value, '-P', script], False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('must explicitly be ON or OFF', result.stderr)
        missing = self.run_command([*command, '-P', script], False)
        self.assertNotEqual(missing.returncode, 0)
        for value, expected in [('off', 'OFF'), ('false', 'OFF'), ('0', 'OFF'), ('on', 'ON'), ('true', 'ON'), ('1', 'ON')]:
            with self.subTest(value=value):
                self.run_command([*command, '-DOPENMS4_SOURCE_DIRTY=' + value, '-P', script])
                self.assertEqual((self.root / 'dirty.txt').read_text(), expected)

    @unittest.skipUnless(shutil.which('git'), 'Git is required')
    def test_native_target_rejects_untracked_inputs_before_compilation(self):
        (self.source / 'CMakeLists.txt').write_text(f'''cmake_minimum_required(VERSION 3.24)
project(GuardedConsumer LANGUAGES CXX)
include("{self.helper}")
openms4_source_revision(revision dirty)
add_library(native STATIC source.cpp)
''')
        (self.source / 'source.cpp').write_text('#error Native compilation must not run after source identity changes\n')
        self.run_command(['git', 'init'])
        self.run_command(['git', 'add', '.'])
        self.run_command(['git', '-c', 'user.name=Contract test', '-c', 'user.email=test@example.invalid',
                          'commit', '-m', 'fixture'])
        self.run_command(['cmake', '-S', self.source, '-B', self.root / 'build'])
        self.run_command(['cmake', '--build', self.root / 'build', '--target', 'GuardedConsumer_source_identity'])
        (self.source / 'new.cpp').write_text('int additional_input;\n')
        result = self.run_command(['cmake', '--build', self.root / 'build', '--target', 'native'], False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('rerun CMake before building', ' '.join((result.stdout + result.stderr).split()))
        self.assertNotIn('Native compilation must not run', result.stdout + result.stderr)


if __name__=='__main__':unittest.main()
