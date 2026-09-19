import concurrent.futures
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

work = Path('/scratch/kohlbach/openms4-resume-final-39ff564483bf/work')
source = work.parent / 'source/packages/flashtnt'
assert subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip() == '4ca4e73a975152f863084ddb8576d40f1241133a'
fixture = source / 'tests/data/aqpz'
output = work.parent / 'flashtnt-repeatability'
output.mkdir(exist_ok=False)
executable = work / 'sdk/bin/FLASHTnT'
parameters = json.loads((fixture / 'FTnT_parameters.json').read_text())
environment = dict(os.environ, OPENMS_DISABLE_UPDATE_CHECK='ON',
                   LD_LIBRARY_PATH='/scratch/kohlbach/openms4-5d1e239-20260910/deps/lib')

def run(settings):
    threads, repeat = settings
    directory = output / f't{threads}-r{repeat}'
    directory.mkdir()
    command = [str(executable), '-in', str(fixture/'out_deconv.mzML'),
               '-fasta', str(fixture/'database.fasta'), '-threads', str(threads)]
    for key, filename in [('out_tag','tags.tsv'), ('out_pro','protein.tsv'), ('out_prsm','prsms.tsv')]:
        command.extend(['-'+key, str(directory/filename)])
    for key, value in parameters.items():
        command.extend(['-'+key, *str(value).splitlines()])
    start = time.monotonic()
    with (directory/'run.log').open('w') as log:
        subprocess.run(command, env=dict(environment, OMP_NUM_THREADS=str(threads)),
                       stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
    result = {'threads':threads, 'repeat':repeat, 'wall_seconds':time.monotonic()-start,
              'command':command, 'tables':{}}
    for filename in ['tags.tsv','protein.tsv','prsms.tsv']:
        path = directory / filename
        with path.open(newline='') as stream:
            rows = list(csv.DictReader(stream, delimiter='\t'))
        canonical = '\n'.join(sorted(json.dumps(row,sort_keys=True) for row in rows))
        result['tables'][filename] = {'rows':len(rows),
            'byte_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'row_order_independent_sha256':hashlib.sha256(canonical.encode()).hexdigest()}
    return result

settings = [(threads, repeat) for threads in (1,2,8) for repeat in (1,2,3)]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    runs = list(pool.map(run, settings))
report = {'source_revision':subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip(),
          'executable_sha256':hashlib.sha256(executable.read_bytes()).hexdigest(),
          'fixture_sha256':{name:hashlib.sha256((fixture/name).read_bytes()).hexdigest()
                           for name in ('out_deconv.mzML','database.fasta','FTnT_parameters.json')},
          'host':'IBMI dax', 'concurrent_runs':3, 'runs':runs,
          'limits':['Run times are concurrent smoke-test observations, not scaling benchmarks.',
                    'This checks same-revision repeatability, not historical numerical parity.']}
report['identical_bytes'] = all(len({r['tables'][name]['byte_sha256'] for r in runs}) == 1
                                for name in runs[0]['tables'])
report['identical_rows'] = all(len({r['tables'][name]['row_order_independent_sha256'] for r in runs}) == 1
                               for name in runs[0]['tables'])
(output/'result.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'identical_bytes':report['identical_bytes'], 'identical_rows':report['identical_rows'],
                  'result':str(output/'result.json')}))

assert report["identical_bytes"] and report["identical_rows"], "Outputs differ across repetitions or thread counts"
