"""Configure actual consumer CMake projects against an isolated mock SDK; do not compile."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from test_split import PACKAGES

class ConsumerConfigure(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.sdk=self.root/'sdk';self.sdk.mkdir()
        (self.sdk/'support.cpp').write_text('// configure-only fixture\n')
        self.config('OpenMS','4.0.0', '''set(OpenMS_SOURCE_REVISION "'''+ 'a'*40+'''")
set(OpenMS_VERSION 4.0.0)
set(OpenMS_WITH_OPENSWATH ON)
set(OpenMS_WITH_WNETALIGN OFF)
set(OpenMS_TEST_SUPPORT_SOURCE "${CMAKE_CURRENT_LIST_DIR}/../../../support.cpp")
foreach(name Core OpenSwathAlgo Arrow TestFramework)
  if(NOT TARGET OpenMS::${name})
    add_library(OpenMS::${name} INTERFACE IMPORTED)
  endif()
endforeach()
''')
        self.config('OpenMSCLI','1.0.0','set(OpenMSCLI_SOURCE_REVISION "'+'b'*40+'")\nif(NOT TARGET OpenMS::CLI)\n add_library(OpenMS::CLI INTERFACE IMPORTED)\nendif()\n')
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
    def configure(self,package,testing=False):
        return subprocess.run(['cmake','-S',str(PACKAGES/package),'-B',str(self.root/'build'),f'-DCMAKE_PREFIX_PATH={self.sdk}',f'-DOPENMS4_DEPENDENCY_LOCK_FILE={self.lock}','-DOPENMS4_SOURCE_REVISION='+'c'*40,'-DCMAKE_FIND_PACKAGE_PREFER_CONFIG=ON','-DCMAKE_INSTALL_BINDIR=custom-bin','-DBUILD_TESTING='+('ON' if testing else 'OFF')],text=True,capture_output=True)
    def check(self,package,testing=False):
        result=self.configure(package,testing);self.assertEqual(result.returncode,0,result.stdout+result.stderr)
    def test_cli_configuration(self):self.check('cli',True)
    def test_topp_configuration_and_manifest_paths(self):
        self.check('topp',True)
        self.assertIn('\tbin/FileInfo',(self.root/'build/share/openms4/tools/topp.tools.tsv').read_text())
        self.assertIn('\tcustom-bin/FileInfo',(self.root/'build/install-manifests/topp.tools.tsv').read_text())
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

if __name__=='__main__':unittest.main()
