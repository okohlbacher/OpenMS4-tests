from pathlib import Path
import json,os,subprocess,time
root=Path(__file__).resolve().parent; workspace=root.parent
env={k:v for k,v in os.environ.items() if not k.startswith('DYLD_') and k not in {'OPENMS_DATA_PATH','OPENMS_HOME_PATH','OPENMS_TOOL_PREFIX_PATH','TOOL_PREFIX_PATH','CMAKE_PREFIX_PATH'}}
env.update(OMP_NUM_THREADS='2',OPENMS_DISABLE_UPDATE_CHECK='ON')
command=['/usr/bin/sandbox-exec','-f',str(workspace/'topp-sdk-validation/isolated-sdk.sb'),'/usr/bin/env','DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/Cellar/abseil/20260107.1/lib','/opt/homebrew/bin/ctest','--test-dir',str(root/'metadata-tests'),'--parallel','4','--timeout','120','--output-on-failure','--output-junit',str(root/'metadata.xml')]
start=time.perf_counter()
with (root/'logs/metadata.log').open('w') as log:result=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
record={'command':command,'exit_code':result.returncode,'wall_seconds':time.perf_counter()-start}
(root/'metadata-run.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
raise SystemExit(result.returncode)
