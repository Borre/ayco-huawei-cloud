#!/usr/bin/env python3
"""load-all-data.py — Seed DWS con esquemas + datos CSV + risk_results.
Ejecutar DESPUÉS de crear el cluster DWS.

Uso: python3 load-all-data.py --host <DWS_IP> --port 8000 --db ayco_db --user ayco_admin --password AycoD3mo2026!
"""

import argparse
import csv
import os
import sys
from pathlib import Path
import psycopg2

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SCRIPTS_DIR = BASE_DIR


def run_sql_file(conn, filepath, description):
    """Execute a SQL file against the connection."""
    print(f"\n{'='*60}")
    print(f"  {description}: {filepath.name}")
    print(f"{'='*60}")
    sql = filepath.read_text()
    with conn.cursor() as cur:
        # Split by semicolons, but handle multi-line statements
        statements = []
        current = []
        for line in sql.split('\n'):
            # Skip comments and empty lines at top level
            stripped = line.strip()
            if stripped.startswith('--'):
                continue
            current.append(line)
            if stripped.endswith(';') and not stripped.startswith('--'):
                statements.append('\n'.join(current))
                current = []
        if current:
            statements.append('\n'.join(current))

        executed = 0
        for stmt in statements:
            stmt = stmt.strip()
            if not stmt:
                continue
            try:
                cur.execute(stmt)
                executed += 1
            except Exception as e:
                # Gracefully handle "already exists", "duplicate", etc.
                err_str = str(e).lower()
                if 'already exists' in err_str or 'duplicate' in err_str:
                    print(f"  [SKIP] {e}")
                else:
                    print(f"  [ERROR] {e}")
                    conn.rollback()
                    # Re-create cursor after rollback
                    cur = conn.cursor()
                    # Don't re-raise — continue with next statement
        conn.commit()
        print(f"  → {executed} statements executed")


def load_csv_to_table(conn, csv_path, table_name):
    """Load a CSV file into a DWS table."""
    print(f"\n  Loading {csv_path.name} → {table_name}...")
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print(f"  → Empty CSV, skipping")
        return 0

    columns = list(rows[0].keys())
    col_list = ', '.join(columns)
    placeholders = ', '.join(['%s'] * len(columns))
    insert_sql = f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders})"

    with conn.cursor() as cur:
        batch_size = 500
        total = 0
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            batch_tuples = []
            for row in batch:
                vals = []
                for col in columns:
                    v = row[col]
                    if v == '' or v is None:
                        vals.append(None)
                    else:
                        vals.append(v)
                batch_tuples.append(tuple(vals))
            try:
                import psycopg2.extras
                psycopg2.extras.execute_values(cur, insert_sql, batch_tuples, template=None, page_size=batch_size)
                conn.commit()
                total += len(batch)
            except Exception as e:
                conn.rollback()
                # Fallback: insert one by one
                print(f"  Batch insert failed, trying row-by-row... ({e})")
                cur2 = conn.cursor()
                for vals in batch_tuples:
                    try:
                        cur2.execute(insert_sql, vals)
                        conn.commit()
                        total += 1
                    except Exception as e2:
                        conn.rollback()
                        print(f"  [SKIP row] {e2}")
                        cur2 = conn.cursor()
        print(f"  → {total} rows loaded into {table_name}")
        return total


def main():
    parser = argparse.ArgumentParser(description="Seed DWS with all demo data")
    parser.add_argument("--host", required=True, help="DWS private IP")
    parser.add_argument("--port", default=8000, type=int)
    parser.add_argument("--db", default="ayco_db")
    parser.add_argument("--user", default="ayco_admin")
    parser.add_argument("--password", default="AycoD3mo2026!")
    parser.add_argument("--skip-schema", action="store_true", help="Skip schema SQL")
    parser.add_argument("--skip-csv", action="store_true", help="Skip CSV loading")
    parser.add_argument("--skip-risk", action="store_true", help="Skip risk results seed")
    args = parser.parse_args()

    print(f"Connecting to DWS: {args.host}:{args.port}/{args.db} as {args.user}")

    conn = psycopg2.connect(
        host=args.host,
        port=args.port,
        dbname=args.db,
        user=args.user,
        password=args.password,
        connect_timeout=30,
    )
    conn.autocommit = False
    print("  ✓ Connected!\n")

    # Step 1: Run schema SQL
    if not args.skip_schema:
        schema_file = SCRIPTS_DIR / "seed-dws.sql"
        if schema_file.exists():
            run_sql_file(conn, schema_file, "Schema + tables + views")
        else:
            print(f"  WARNING: {schema_file} not found, skipping")

    # Step 2: Load CSV data
    if not args.skip_csv:
        mappings = [
            ("vendors.csv", "ods.vendors"),
            ("customers.csv", "ods.customers"),
            ("transactions.csv", "ods.transactions"),
        ]
        for csv_file, table in mappings:
            csv_path = DATA_DIR / csv_file
            if csv_path.exists():
                load_csv_to_table(conn, csv_path, table)
            else:
                print(f"\n  WARNING: {csv_path} not found, skipping")

    # Step 3: Seed risk_results
    if not args.skip_risk:
        risk_file = DATA_DIR / "seed_risk_results.sql"
        if risk_file.exists():
            run_sql_file(conn, risk_file, "Risk results seed data")
        else:
            print(f"\n  WARNING: {risk_file} not found, skipping")

    conn.close()
    print(f"\n{'='*60}")
    print(f"  DWS seeding complete!")
    print(f"{'='*60}")
    print(f"\n  Next: update api.service DWS_HOST → {args.host}")
    print(f"  Then:  systemctl daemon-reload && systemctl restart api")
    print()


if __name__ == "__main__":
    main()
