"""Create the BigQuery dataset/tables and load the generated CSVs. CREATES CLOUD RESOURCES - run it yourself.

    python -m app.data.generate
    python -m scripts.load_bigquery --project YOUR_PROJECT [--dataset linesleuth_demo] [--location asia-southeast1]

Tables are replaced on every run (WRITE_TRUNCATE) except work_orders, which is only created if missing.
"""
from __future__ import annotations

import argparse

from app.config import DATA_DIR

SCHEMAS = {
    "sensor_readings": [("row_id", "STRING"), ("scenario_id", "STRING"), ("ts", "DATETIME"), ("line", "INT64"),
                        ("machine", "STRING"), ("sensor", "STRING"), ("value", "FLOAT64"), ("unit", "STRING")],
    "events": [("row_id", "STRING"), ("scenario_id", "STRING"), ("ts", "DATETIME"), ("line", "INT64"),
               ("machine", "STRING"), ("event_type", "STRING"), ("code", "STRING"), ("severity", "STRING"),
               ("actor", "STRING"), ("message", "STRING")],
    "sensor_catalog": [("row_id", "STRING"), ("machine", "STRING"), ("machine_name", "STRING"), ("sensor", "STRING"),
                       ("unit", "STRING"), ("normal_low", "FLOAT64"), ("normal_high", "FLOAT64"), ("sop_section", "STRING")],
}
WORK_ORDERS = [("wo_id", "STRING"), ("created_at", "DATETIME"), ("scenario_id", "STRING"), ("investigation_id", "STRING"),
               ("line", "INT64"), ("machine", "STRING"), ("root_cause_key", "STRING"), ("root_cause", "STRING"),
               ("confidence", "STRING"), ("priority", "STRING"), ("agent_mode", "STRING"), ("payload_json", "STRING")]


def main() -> None:
    from google.cloud import bigquery

    p = argparse.ArgumentParser()
    p.add_argument("--project", required=True)
    p.add_argument("--dataset", default="linesleuth_demo")
    p.add_argument("--location", default="asia-southeast1")
    a = p.parse_args()

    client = bigquery.Client(project=a.project)
    ds = bigquery.Dataset(f"{a.project}.{a.dataset}")
    ds.location = a.location
    client.create_dataset(ds, exists_ok=True)
    for table, cols in SCHEMAS.items():
        schema = [bigquery.SchemaField(n, t) for n, t in cols]
        cfg = bigquery.LoadJobConfig(schema=schema, source_format=bigquery.SourceFormat.CSV, skip_leading_rows=1,
                                     write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE)
        with open(DATA_DIR / f"{table}.csv", "rb") as f:
            job = client.load_table_from_file(f, f"{a.project}.{a.dataset}.{table}", job_config=cfg)
        job.result()
        print(f"loaded {table}: {client.get_table(f'{a.project}.{a.dataset}.{table}').num_rows} rows")
    wo = bigquery.Table(f"{a.project}.{a.dataset}.work_orders", schema=[bigquery.SchemaField(n, t) for n, t in WORK_ORDERS])
    client.create_table(wo, exists_ok=True)
    print("work_orders table ready")


if __name__ == "__main__":
    main()
