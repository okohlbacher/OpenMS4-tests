import json
from pathlib import Path
import re
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]

class PackagePins(unittest.TestCase):
    def test_every_submodule_matches_parent_lock(self):
        lock=json.loads((ROOT/'packages.lock.json').read_text())['packages']
        self.assertEqual(len(lock),18)
        for name,entry in lock.items():
            head=subprocess.run(['git','-C',str(ROOT/entry['path']),'rev-parse','HEAD'],text=True,capture_output=True,check=True).stdout.strip()
            self.assertEqual(head,entry['source_revision'],name)
            index=subprocess.run(['git','-C',str(ROOT),'ls-files','--stage','--',entry['path']],text=True,capture_output=True,check=True).stdout.split()
            self.assertEqual(index[:2],['160000',head],name)
    def test_consumers_pin_the_selected_dependency_commits(self):
        packages=json.loads((ROOT/'packages.lock.json').read_text())['packages']
        names={'OpenMS':'core','OpenMSCLI':'cli','OpenMSTestData':'test-data','pyopenms':'pyopenms','OpenMSFLASH':'flash','OpenMSTOPP':'topp','OpenMSProSE':'prose','FLASHTnT':'flashtnt'}
        for name in packages:
            path=ROOT/packages[name]['path']/'dependencies.lock.json'
            if not path.exists():
                self.assertEqual(name,'core');continue
            for dependency,entry in json.loads(path.read_text())['dependencies'].items():
                self.assertRegex(entry['source_revision'],r'^[0-9a-f]{40}$')
                if not packages[name].get('frozen_dependencies', False):
                    self.assertEqual(entry['source_revision'],packages[names[dependency]]['source_revision'],f'{name}->{dependency}')
    def test_every_package_carries_the_current_graph_section(self):
        # Each package repository is standalone, so it ships its own copy of the figure and of
        # the generated section naming its dependencies and consumers; both follow the locks.
        result=subprocess.run(['python3',str(ROOT/'tools'/'sync_package_docs.py'),'--check'],text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

if __name__=='__main__':unittest.main()
