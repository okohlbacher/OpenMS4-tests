from pathlib import Path
import json,os,subprocess,time
root=Path(__file__).resolve().parent; workspace=root.parent; sdk=workspace/'topp-sdk-validation/sdk'; build=root/'regressions'
env={k:v for k,v in os.environ.items() if not k.startswith('DYLD_') and k not in {'OPENMS_DATA_PATH','OPENMS_HOME_PATH','OPENMS_TOOL_PREFIX_PATH','TOOL_PREFIX_PATH','CMAKE_PREFIX_PATH'}}
env.update(OMP_NUM_THREADS='2',OPENMS_DISABLE_UPDATE_CHECK='ON')
prefix=['/usr/bin/sandbox-exec','-f',str(workspace/'topp-sdk-validation/isolated-sdk.sb'),'/usr/bin/env','DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/Cellar/abseil/20260107.1/lib']
commands=[('configure',['/opt/homebrew/bin/cmake','-S',str(workspace/'topp-sdk-validation/test-data-sdk/share/openms4-test-data/1.0.0'),'-B',str(build),f'-DCMAKE_PREFIX_PATH={sdk}','-DOPENMS4_REGRESSION_TESTS=ON','-DOPENMS4_REQUIRE_CLEAN_SOURCE=ON',f'-DOPENMS4_TOOLS_BIN={sdk/"bin"}'])]
for name,jobs in [('parallel',4),('serial',1)]:
    commands.append((name,['/opt/homebrew/bin/ctest','--test-dir',str(build),'--tests-from-file',str(root/f'regression-{name}-tests.txt'),'--parallel',str(jobs),'--timeout','300','--output-on-failure','--output-junit',str(root/f'numerical-{name}.xml')]))
records=[]
for name,command in commands:
    actual=prefix+command; start=time.perf_counter(); print('Starting',name,flush=True)
    with (root/f'logs/numerical-{name}.log').open('w') as log:result=subprocess.run(actual,env=env,stdout=log,stderr=subprocess.STDOUT)
    records.append({'phase':name,'command':actual,'exit_code':result.returncode,'wall_seconds':time.perf_counter()-start})
    (root/'numerical-run.json').write_text(json.dumps(records,indent=2)+'\n'); print(name,records[-1]['exit_code'],records[-1]['wall_seconds'],flush=True)
    if name=='configure' and result.returncode:raise SystemExit(result.returncode)
    if name=='configure':
        inventory=json.loads(subprocess.check_output(prefix+['/opt/homebrew/bin/ctest','--test-dir',str(build),'--show-only=json-v1'],env=env,text=True))['tests']
        names={t['name'] for t in inventory}
        selected=set((root/'regression-tests.txt').read_text().splitlines())
        assert len(selected)==1306 and selected <= names,(len(selected),selected-names)
        by_name={t['name']:t for t in inventory}
        for test_name in selected:
            props={p['name']:p['value'] for p in by_name[test_name].get('properties',[])}
            dependencies=props.get('DEPENDS',[])
            if isinstance(dependencies,str):dependencies=dependencies.split(';')
            assert set(dependencies) <= selected,(test_name,set(dependencies)-selected)
        (root/'fresh-inventory-summary.json').write_text(json.dumps({'registered':len(names),'selected':len(selected),'declared_dependency_closure':True},indent=2)+'\n')
raise SystemExit(any(r['exit_code'] for r in records))
