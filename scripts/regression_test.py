"""Run the cheap offline gates that must stay green after every change."""
import os
import subprocess
import sys
from pathlib import Path


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(*args, env=None):
    subprocess.run(args, cwd=ROOT, env=env, check=True)


run(sys.executable, "scripts/phase_a_test.py")
run(sys.executable, "scripts/phase_b_test.py")
run(sys.executable, "scripts/phase_c_test.py")
run(sys.executable, "scripts/phase_d_test.py")
provider_env = {**os.environ, "PYTHONPATH": "apps"}
run(sys.executable, "scripts/provider_contract_test.py", env=provider_env)
run(sys.executable, "-m", "py_compile", *map(str, Path(ROOT, "apps/api/attic_api").glob("*.py")))
print("offline regression ok")
