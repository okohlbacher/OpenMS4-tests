"""Repeated process-wall-time measurements of the existing TICCalculator modes."""
from pathlib import Path
import datetime,hashlib,json,math,os,re,statistics,subprocess,time
root=Path(__file__).resolve().parent; workspace=root.parent; sdk=workspace/'topp-sdk-validation/sdk'
input_info=json.loads((root/'benchmark-input.json').read_text()); source=Path(input_info['input_path'])
assert hashlib.sha256(source.read_bytes()).hexdigest()==input_info['input_sha256']
env={k:v for k,v in os.environ.items() if not k.startswith('DYLD_') and k not in {'OPENMS_DATA_PATH','OPENMS_HOME_PATH','OPENMS_TOOL_PREFIX_PATH','TOOL_PREFIX_PATH','CMAKE_PREFIX_PATH'}}
env.update(DYLD_FALLBACK_LIBRARY_PATH='/opt/homebrew/Cellar/abseil/20260107.1/lib',OPENMS_DISABLE_UPDATE_CHECK='ON')
records=[]

def execute(command,label,validate=True):
    start=time.perf_counter()
    result=subprocess.run(command,env=env,cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180)
    elapsed=time.perf_counter()-start
    (root/'benchmarks'/f'{label}.log').write_text(result.stdout)
    entry={'command':command,'wall_seconds':elapsed,'exit_code':result.returncode,'log':f'benchmarks/{label}.log'}
    if result.returncode:raise RuntimeError(f'{label}: exit {result.returncode}')
    if validate:
        counts=re.search(r'There are (\d+) spectra and (\d+) peaks in the input file\.',result.stdout)
        tic=re.search(r'The total ion current is ([\d.eE+\-]+)',result.stdout)
        if not counts or not tic:raise RuntimeError(f'{label}: missing science output despite zero exit status')
        entry.update(spectra=int(counts[1]),peaks=int(counts[2]),printed_tic=float(tic[1]))
        if (entry['spectra'],entry['peaks'])!=(input_info['spectra'],input_info['peaks']):raise RuntimeError(f'{label}: wrong counts')
        expected=float(input_info['tic_calculator_expected_printed_tic'])
        if entry['printed_tic']!=expected:raise RuntimeError(f'{label}: wrong TIC at printed precision')
        if re.search(r'(?im)\b(error:|exception:|library not loaded|segmentation fault)',result.stdout):raise RuntimeError(f'{label}: error diagnostic')
    return entry

cache=execute(input_info['cache_creation_command'],'cache-create',validate=False)
for p in input_info['cache_expected_files']:assert Path(p).is_file() and Path(p).stat().st_size>0
cache['files']={str(Path(p).name):{'bytes':Path(p).stat().st_size,'sha256':hashlib.sha256(Path(p).read_bytes()).hexdigest()} for p in input_info['cache_expected_files']}
(root/'cache-creation.json').write_text(json.dumps(cache,indent=2)+'\n')
methods=input_info['methods']; cells=[(m,t) for m in methods for t in (1,2)]
# Warm every cell once, then rotate the execution order each round to spread host drift.
for iteration in range(6):
    ordered=cells[iteration%len(cells):]+cells[:iteration%len(cells)]
    for method,threads in ordered:
        input_path=root/'input.cachedMzML' if method.startswith('cached') else source
        command=[str(sdk/'bin/TICCalculator'),'-in',str(input_path),'-read_method',method,'-loadData','true','-threads',str(threads)]
        env['OMP_NUM_THREADS']=str(threads)
        label=f'{method}-t{threads}-'+('warmup' if iteration==0 else f'repeat{iteration}')
        entry=execute(command,label); entry.update(method=method,threads=threads,warmup=iteration==0,iteration=iteration)
        records.append(entry)
        (root/'benchmark-runs.json').write_text(json.dumps(records,indent=2)+'\n')
        print(label,f'{entry["wall_seconds"]:.4f}s',flush=True)
summary=[]
for method,threads in cells:
    times=[r['wall_seconds'] for r in records if r['method']==method and r['threads']==threads and not r['warmup']]
    assert len(times)==5
    summary.append({'method':method,'threads':threads,'repetitions':len(times),'median_seconds':statistics.median(times),'min_seconds':min(times),'max_seconds':max(times),'stdev_seconds':statistics.stdev(times)})
(root/'benchmark-summary.json').write_text(json.dumps({'finished_at':datetime.datetime.now().astimezone().isoformat(),'clock':'time.perf_counter','includes_process_startup':True,'warmups_per_cell':1,'cache_creation_seconds':cache['wall_seconds'],'results':summary},indent=2)+'\n')
