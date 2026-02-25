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

import os
from pathlib import Path
from dbt.cli.main import dbtRunner

PROJECT_DIR = Path(__file__).parent / "jaffle-shop"
os.chdir(PROJECT_DIR)

runner = dbtRunner()

for args in [
    ["deps"],
    ["seed", "--profiles-dir", ".", "--vars", "{load_source_data: true}"],
    ["build", "--profiles-dir", ".", "--vars", "{load_source_data: true}"],
]:
    print(f"\nRunning: dbt {' '.join(args)}")
    res = runner.invoke(args)
    if not res.success:
        raise RuntimeError(f"dbt {args[0]} failed: {res.exception}")

db = Path("../jaffle_shop.duckdb").resolve()
print(f"\nDone. Built {db}")
