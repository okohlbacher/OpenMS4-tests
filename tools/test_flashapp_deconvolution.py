"""Real local FLASHApp deconvolution integration; no GUI or queue simulation."""
import argparse
from pathlib import Path
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time

PACKAGES = Path(__file__).resolve().parents[1] / 'packages'
APP = PACKAGES / 'flashapp'
sys.path.insert(0, str(APP))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk-prefix', type=Path, required=True)
    parser.add_argument('--work-dir', type=Path, required=True)
    args = parser.parse_args()
    sdk = args.sdk_prefix.resolve()
    run = args.work_dir.resolve()
    if run.exists():
        parser.error('--work-dir must not exist')
    run.mkdir(parents=True)
    sys.path.insert(0, str(sdk))
    os.environ['PATH'] = str(sdk / 'bin') + os.pathsep + os.environ.get('PATH', '')
    import pyopenms as oms
    import streamlit as st
    from src.Workflow import DeconvWorkflow

    lock = json.loads((APP / 'dependencies.lock.json').read_text())['dependencies']
    assert Path(oms.__file__).resolve().parent == sdk / 'pyopenms'
    assert oms.__source_revision__ == lock['pyopenms']['source_revision']
    assert oms.__openms_core_revision__ == lock['OpenMS']['source_revision']
    sdk_info = json.loads((sdk / 'lib/cmake/OpenMS/OpenMSBuildInfo.json').read_text())
    assert json.loads(oms.VersionInfo.getBuildInfo()) == sdk_info
    assert not sdk_info['source_dirty']
    sample = run / 'FLASHDeconv_sample_input.mzML'
    shutil.copy2(sdk / 'share/openms4-test-data/1.0.0/topp' / sample.name, sample)
    st.session_state['workspace'] = str(run)
    st.session_state['settings'] = {'online_deployment': False, 'max_threads': {'local': 2, 'online': 2}}
    workflow = DeconvWorkflow()
    manager = workflow.parameter_manager
    assert manager.create_ini('FLASHDeconv')
    assert (manager.ini_dir/'FLASHDeconv.ini').is_file()
    st.session_state[manager.param_prefix+'mzML-files'] = [str(sample)]
    st.session_state[manager.param_prefix+'max_threads'] = 2
    st.session_state[manager.topp_param_prefix+'FLASHDeconv:1:test'] = True
    manager.save_parameters()
    parameters = manager.get_topp_parameters('FLASHDeconv')
    assert parameters['test'] is True
    assert 'FD:report_FDR' in parameters
    workflow.params = manager.get_parameters_from_json()
    begin = time.monotonic()
    assert workflow.execution() is True
    datasets = workflow.file_manager.get_results_list(['scan_table', 'mass_table', 'out_tsv'])
    assert len(datasets) == 1, datasets
    dataset = datasets[0]
    results = workflow.file_manager.get_results(dataset, ['scan_table', 'mass_table', 'out_tsv', 'out_deconv_mzML', 'anno_annotated_mzML'])
    assert len(results['scan_table']) > 0
    assert len(results['mass_table']) > 0
    densities = workflow.file_manager.get_results(dataset, ['density_target', 'density_decoy'])
    assert densities['density_target'].empty and densities['density_decoy'].empty
    comparison_spec = importlib.util.spec_from_file_location('compare_features', PACKAGES/'flash/tests/compare_features.py')
    comparison = importlib.util.module_from_spec(comparison_spec)
    comparison_spec.loader.exec_module(comparison)
    reference = PACKAGES/'flash/tests/data/FLASHDeconv_sample_pre_refactor.tsv'
    comparison.compare(results['out_tsv'], reference)
    # Exercise another real tool through the same command/INI boundary.
    assert manager.create_ini('FuzzyDiff')
    copied_output = run/'reference-copy.tsv'
    shutil.copy2(results['out_tsv'], copied_output)
    assert workflow.executor.run_topp('FuzzyDiff', {'in1':[results['out_tsv']], 'in2':[str(copied_output)]}) is True
    missing = run/'does-not-exist.mzML'
    try:
        workflow.executor.run_topp('FLASHDeconv', {'in':[str(missing)], 'out':[str(run/'missing.tsv')]})
    except subprocess.CalledProcessError as error:
        assert error.returncode == 1, (error.returncode, error.stderr)
        diagnostic = (workflow.workflow_dir/'logs/all.log').read_text()
        assert str(missing) in diagnostic and 'Error: File not found' in diagnostic, diagnostic[-2000:]
    else:
        raise AssertionError('Missing input was reported as success')
    assert not list(workflow.executor.pid_dir.iterdir())
    record = {
        'app_source_revision': subprocess.check_output(['git','-C',str(APP),'rev-parse','HEAD'],text=True).strip(),
        'python_source_revision': oms.__source_revision__, 'core_source_revision': oms.__openms_core_revision__,
        'scope': 'real local non-UI DeconvWorkflow.execution, INI creation/pyOpenMS parsing, persisted parameters, cached parsing, FLASHDeconv and FuzzyDiff run_topp, intended missing-input failure',
        'deployment': 'fresh installed Release SDK and products; third-party dependencies in the recorded isolated environment; no container or repaired wheel claim',
        'workspace': str(run), 'dataset': dataset, 'scan_rows': len(results['scan_table']), 'mass_table_rows':len(results['mass_table']),
        'feature_reference': str(reference), 'feature_columns_compared': len(comparison.COLUMNS),
        'duration_seconds': round(time.monotonic()-begin,3), 'returncode':0,
        'workflow_execution_success': True,
    }
    (run / 'result.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2),flush=True)
    workflow.file_manager.cache_connection.close()


if __name__ == '__main__':
    main()
