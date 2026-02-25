# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#     "dbt-core",
#     "dbt-duckdb",
# ]
# ///
"""Build jaffle_shop.duckdb by running dbt against the jaffle-shop submodule.

    uv run setup.py
"""

import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).parent / "jaffle-shop"
DBT_VARS = "{load_source_data: true}"

for cmd in [
    ["dbt", "deps"],
    ["dbt", "seed", "--profiles-dir", ".", "--vars", DBT_VARS],
    ["dbt", "build", "--profiles-dir", ".", "--vars", DBT_VARS],
]:
    print(f"\nRunning: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=PROJECT_DIR, check=True)

db = Path(__file__).parent / "jaffle_shop.duckdb"
print(f"\nDone. Built {db}")
