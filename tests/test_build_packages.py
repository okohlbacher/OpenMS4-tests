"""The native runner must order installed dependencies before their consumers."""
from graphlib import TopologicalSorter
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_packages', ROOT / 'tools/build_packages.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class NativeBuildGraph(unittest.TestCase):
    def test_complete_graph_respects_installed_sdk_dependencies(self):
        packages = json.loads((ROOT / 'packages.lock.json').read_text())['packages']
        graph = runner.native_graph(packages)
        order = list(TopologicalSorter(graph).static_order())
        self.assertEqual(set(order), set(packages) - {'core', 'flashapp'})
        for consumer, dependencies in graph.items():
            for dependency in dependencies:
                self.assertLess(order.index(dependency), order.index(consumer))
        self.assertTrue({'flash', 'prose'} <= graph['pyopenms'])
        self.assertIn('cli', graph['topp'])


if __name__ == '__main__':
    unittest.main()
