#!/usr/bin/env python3
"""Compatibility entry point for FLASHApp's canonical artifact verifier."""
import importlib.util
from pathlib import Path

implementation = Path(__file__).resolve().parents[1] / 'packages/flashapp/experimental/verify_artifacts.py'
spec = importlib.util.spec_from_file_location('openms4_app_artifacts', implementation)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
verified_artifacts = module.verified_artifacts
extract_runtime = module.extract_runtime
main = module.main

if __name__ == '__main__':
    main()
