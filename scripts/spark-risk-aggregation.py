"""risk_aggregation.py — DLI Spark job for contract risk aggregation.

Run via: spark-submit --deploy-mode cluster risk_aggregation.py
Or via DLI Spark Job API with app_parameters.

Queries DLI tables (contracts + risk_results) and produces
aggregated risk metrics stored back to OBS.
"""

import sys
import json
import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# When running on DLI, pyspark is available
try:
    from pyspark.sql import SparkSession
except ImportError:
    logger.error("pyspark not available — run on DLI Spark cluster")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", default="ayco_contracts")
    parser.add_argument("--output", default="obs://ayco-contracts-results/aggregated/")
    args = parser.parse_args()

    spark = SparkSession.builder \
        .appName("AYCO Risk Aggregation") \
        .config("spark.sql.catalogImplementation", "hive") \
        .enableHiveSupport() \
        .getOrCreate()

    # Use DLI catalog
    spark.sql(f"USE {args.database}")

    # ─── Query 1: Risk summary by level ────────────────────────────
    risk_summary = spark.sql("""
        SELECT
            risk_level,
            COUNT(*) as contract_count,
            AVG(risk_score) as avg_risk_score,
            MIN(risk_score) as min_risk_score,
            MAX(risk_score) as max_risk_score
        FROM risk_results
        GROUP BY risk_level
        ORDER BY avg_risk_score DESC
    """)

    # ─── Query 2: High-risk contracts ─────────────────────────────
    high_risk = spark.sql("""
        SELECT
            r.contract_number,
            c.contratista,
            c.monto_total,
            r.risk_score,
            r.risk_level,
            r.alertas
        FROM risk_results r
        JOIN contracts c ON r.contract_number = c.contract_number
        WHERE r.risk_score >= 7
        ORDER BY r.risk_score DESC
    """)

    # ─── Query 3: Vendor risk exposure ────────────────────────────
    vendor_exposure = spark.sql("""
        SELECT
            c.contratista as vendor,
            COUNT(*) as total_contracts,
            SUM(CAST(REPLACE(c.monto_total, ',', '') AS DOUBLE)) as total_exposure,
            AVG(r.risk_score) as avg_risk_score
        FROM contracts c
        JOIN risk_results r ON c.contract_number = r.contract_number
        GROUP BY c.contratista
        ORDER BY total_exposure DESC
    """)

    # Write results to OBS
    risk_summary.coalesce(1).write.mode("overwrite").json(f"{args.output}/risk_summary/")
    high_risk.coalesce(1).write.mode("overwrite").json(f"{args.output}/high_risk/")
    vendor_exposure.coalesce(1).write.mode("overwrite").json(f"{args.output}/vendor_exposure/")

    logger.info(f"Aggregation complete. Results written to {args.output}")

    # Print summary for demo (keep print for Spark UI visibility)
    print("\n=== RISK SUMMARY ===")
    risk_summary.show(truncate=False)
    print("\n=== HIGH RISK CONTRACTS ===")
    high_risk.show(truncate=False)
    print("\n=== VENDOR EXPOSURE ===")
    vendor_exposure.show(truncate=False)

    spark.stop()


if __name__ == "__main__":
    main()
