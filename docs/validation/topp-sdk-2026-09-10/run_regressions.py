"""Run a bounded installed TOPP numerical suite using an installed fixture package."""
from pathlib import Path
import json,os,subprocess,time
root=Path(__file__).resolve().parent
sdk=root/'sdk'; build=root/'regressions'; harness=root/'test-data-sdk/share/openms4-test-data/1.0.0'
env={k:v for k,v in os.environ.items() if not k.startswith('DYLD_') and k not in {'OPENMS_DATA_PATH','OPENMS_HOME_PATH','OPENMS_TOOL_PREFIX_PATH','TOOL_PREFIX_PATH','CMAKE_PREFIX_PATH'}}
env.update(DYLD_FALLBACK_LIBRARY_PATH='/opt/homebrew/Cellar/abseil/20260107.1/lib',OMP_NUM_THREADS='2',OPENMS_DISABLE_UPDATE_CHECK='ON')
pattern=r'^TOPP_(IDMerger|IDFilter|NoiseFilterGaussian|NoiseFilterSGolay|MapNormalizer|ConsensusMapNormalizer|MapAlignerPoseClustering|MapAlignerIdentification|MapRTTransformer|FileMerger|DecoyDatabase|TextExporter|FileConverter)_'
commands=[('regression-configure',['/opt/homebrew/bin/cmake','-S',str(harness),'-B',str(build),f'-DCMAKE_PREFIX_PATH={sdk}','-DOPENMS4_REGRESSION_TESTS=ON','-DOPENMS4_REQUIRE_CLEAN_SOURCE=ON',f'-DOPENMS4_TOOLS_BIN={sdk/"bin"}']),('numerical',['/opt/homebrew/bin/ctest','--test-dir',str(build),'-R',pattern,'--parallel','4','--timeout','180','--output-on-failure','--output-junit',str(root/'evidence/numerical.xml')]),('selected-negative',['/opt/homebrew/bin/ctest','--test-dir',str(build),'-R',r'^TOPP_((INI|CLI)_INVALID|PeakPickerHiRes_|FileInfo_)','--parallel','4','--timeout','180','--output-on-failure','--output-junit',str(root/'evidence/selected-negative.xml')])]
results=[]
for name,command in commands:
    print(f'Starting {name}',flush=True); start=time.monotonic()
    actual=['/usr/bin/sandbox-exec','-f',str(root/'isolated-sdk.sb'),'/usr/bin/env','DYLD_FALLBACK_LIBRARY_PATH='+env['DYLD_FALLBACK_LIBRARY_PATH'],*command]
    with (root/f'evidence/{name}.log').open('w') as log:r=subprocess.run(actual,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
    results.append({'phase':name,'command':actual,'exit_code':r.returncode,'elapsed_seconds':time.monotonic()-start})
    (root/'evidence/regression-results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(f'{name}: exit {r.returncode}; {results[-1]["elapsed_seconds"]:.2f}s',flush=True)
    if r.returncode:raise SystemExit(r.returncode)
