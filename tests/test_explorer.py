"""Run the explorer's JavaScript calculation checks (explorer/test_calc.mjs) from pytest."""
import shutil, subprocess
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which('node') is None, reason='node not installed')
def test_explorer_calculations_match_notebook():
    r = subprocess.run(['node', str(ROOT / 'explorer' / 'test_calc.mjs')], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
