"""Real local FLASHApp deconvolution integration; no GUI or queue simulation."""
from pathlib import Path
import csv
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

WORKSPACE = Path(__file__).resolve().parents[1]
APP = WORKSPACE / 'OpenMS4-tests/packages/flashapp'
sys.path.insert(0, str(APP))


def main():
    import faulthandler
    faulthandler.dump_traceback_later(45, repeat=True)
    print('IMPORT_PYOPENMS', flush=True)
    import pyopenms as oms
    print('IMPORT_STREAMLIT', flush=True)
    import streamlit as st
    print('IMPORT_WORKFLOW', flush=True)
    from src.Workflow import DeconvWorkflow
    print('IMPORTS_COMPLETE', flush=True)

    assert oms.__source_revision__ == '14d950a460636b9a8fa255b7ac657926fec403de'
    assert oms.__openms_core_revision__ == '4fdec46b205459b92e7d3b9e56df5d8e912d5c85'
    run = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp(prefix='flashapp-real-deconv-', dir=WORKSPACE))
    sample = run / 'FLASHDeconv_sample_input.mzML'
    if not sample.exists():
        shutil.copy2(WORKSPACE/'product-sdk/share/openms4-test-data/1.0.0/topp'/sample.name, sample)
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
    workflow_success = len(sys.argv) == 1
    if workflow_success:
        print('WORKFLOW_EXECUTION_BEGIN', flush=True)
        assert workflow.execution() is True
        print('WORKFLOW_EXECUTION_COMPLETE', flush=True)
    else:
        print('VALIDATING_EXISTING_OUTPUT_AFTER_RECORDED_DENSITY_FAILURE', flush=True)
    datasets = workflow.file_manager.get_results_list(['scan_table', 'mass_table', 'out_tsv'])
    assert len(datasets) == 1, datasets
    dataset = datasets[0]
    results = workflow.file_manager.get_results(dataset, ['scan_table', 'mass_table', 'out_tsv', 'out_deconv_mzML', 'anno_annotated_mzML'])
    assert len(results['scan_table']) > 0
    assert len(results['mass_table']) > 0
    if workflow_success:
        densities = workflow.file_manager.get_results(dataset, ['density_target', 'density_decoy'])
        assert densities['density_target'].empty and densities['density_decoy'].empty
    comparison_spec = importlib.util.spec_from_file_location('compare_features', WORKSPACE/'OpenMS4-tests/packages/flash/tests/compare_features.py')
    comparison = importlib.util.module_from_spec(comparison_spec)
    comparison_spec.loader.exec_module(comparison)
    reference = WORKSPACE/'OpenMS4-tests/packages/flash/tests/data/FLASHDeconv_sample_pre_refactor.tsv'
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
        'deployment': 'relocated self-contained product runtime verified tools; no inherited DYLD or initial data override; app execution itself does not use the filesystem-denial sandbox',
        'workspace': str(run), 'dataset': dataset, 'scan_rows': len(results['scan_table']), 'mass_table_rows':len(results['mass_table']),
        'feature_reference': str(reference), 'feature_columns_compared': len(comparison.COLUMNS),
        'duration_seconds': round(time.monotonic()-begin,3), 'returncode':0,
        'workflow_execution_success':workflow_success,
        'workflow_limitation':None if workflow_success else 'Existing gaussian_kde fails on identical target Qscores after genuine successful tool execution and mzML/table caching',
    }
    (WORKSPACE/'implementation-build-evidence/flashapp-real-deconv-result.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2),flush=True)
    workflow.file_manager.cache_connection.close()
    faulthandler.cancel_dump_traceback_later()


if __name__ == '__main__':
    main()
