"""Exact local recipe: standalone TOPP archive against copied installed SDK files."""
from pathlib import Path
import json,os,subprocess,time,sys
root=Path(__file__).resolve().parent
record=json.loads((root/'evidence/inputs.json').read_text())
env={k:v for k,v in os.environ.items() if not k.startswith('DYLD_') and k not in {'OPENMS_DATA_PATH','OPENMS_HOME_PATH','OPENMS_TOOL_PREFIX_PATH','TOOL_PREFIX_PATH','CMAKE_PREFIX_PATH'}}
env.update(DYLD_FALLBACK_LIBRARY_PATH='/opt/homebrew/Cellar/abseil/20260107.1/lib',OMP_NUM_THREADS='2',OPENMS_DISABLE_UPDATE_CHECK='ON')
cmake='/opt/homebrew/bin/cmake'; ctest='/opt/homebrew/bin/ctest'; sdk=root/'sdk'; build=root/'build'
commands=[('configure',[cmake,'-S',str(root/'source'),'-B',str(build),'-G','Ninja','-DCMAKE_BUILD_TYPE=Debug','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',f'-DCMAKE_PREFIX_PATH={sdk};/opt/homebrew;/opt/homebrew/opt/libomp',f'-DCMAKE_INSTALL_PREFIX={sdk}','-DCMAKE_FIND_FRAMEWORK=LAST','-DCURL_ROOT=/opt/homebrew/opt/curl','-DLP_SOLVER=COIN','-DBUILD_TESTING=ON','-DOPENMS4_REQUIRE_CLEAN_SOURCE=ON',f'-DOPENMS4_SOURCE_REVISION={record["topp_source_revision"]}','-DOPENMS4_SOURCE_DIRTY=OFF']),('build',[cmake,'--build',str(build),'--parallel','2']),('metadata',[ctest,'--test-dir',str(build),'--parallel','4','--timeout','120','--output-on-failure','--output-junit',str(root/'evidence/metadata.xml')]),('install',[cmake,'--install',str(build)])]
results=[]
for name,command in commands:
    if len(sys.argv) > 1 and name not in sys.argv[1:]:continue
    start=time.monotonic(); print(f'Starting {name}',flush=True)
    actual=['/usr/bin/sandbox-exec','-f',str(root/'isolated-sdk.sb'),'/usr/bin/env','DYLD_FALLBACK_LIBRARY_PATH='+env['DYLD_FALLBACK_LIBRARY_PATH'],*command]
    with (root/f'evidence/{name}.log').open('w') as log:
        result=subprocess.run(actual,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
    results.append({'phase':name,'command':actual,'exit_code':result.returncode,'elapsed_seconds':time.monotonic()-start})
    (root/'evidence/build-results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(f'{name}: exit {result.returncode}; {results[-1]["elapsed_seconds"]:.2f}s',flush=True)
    if result.returncode:raise SystemExit(result.returncode)
