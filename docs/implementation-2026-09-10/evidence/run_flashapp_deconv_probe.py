"""Launch real FLASHApp integration with repaired local artifacts and a bound."""
import os
from pathlib import Path
import subprocess

workspace = Path(__file__).resolve().parents[1]
environment = {key:value for key,value in os.environ.items()
               if not key.startswith('DYLD_') and key not in ('OPENMS_DATA_PATH','PYTHONPATH')}
environment.update(
    PATH=str(workspace/'product runtime verified/bin')+os.pathsep+environment['PATH'],
    PYTHONDONTWRITEBYTECODE='1', PYTHONUNBUFFERED='1', OMP_NUM_THREADS='2',
    FLASH_POSTPROC_WORKERS='1', OPENMS_DISABLE_UPDATE_CHECK='ON',
)
with (workspace/'implementation-build-evidence/flashapp-real-deconv.log').open('w') as log:
    result=subprocess.run(
        ['/private/tmp/openms4-flashapp-test-env/bin/python', str(workspace/'implementation-build-evidence/qualify_flashapp_deconv.py')],
        cwd='/private/tmp', env=environment, stdout=log, stderr=subprocess.STDOUT, timeout=180,
    )
raise SystemExit(result.returncode)
