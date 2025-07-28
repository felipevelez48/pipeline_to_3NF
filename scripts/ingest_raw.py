import os
import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

CSV_PATH = Path("/opt/airflow/data/data_jobs.csv")
TABLE_NAME = "jobs_raw"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

def main() -> None:
    conn_str = os.getenv("AIRFLOW__DATABASE__SQL_ALCHEMY_CONN")
    engine = create_engine(conn_str)

    logging.info("Leyendo %s …", CSV_PATH)
    df = pd.read_csv(CSV_PATH)

    logging.info("Filas leídas: %d", len(df))

    df.to_sql(TABLE_NAME, engine, if_exists="replace", index=False, chunksize=10_000)
    logging.info("Datos cargados en tabla %s", TABLE_NAME)


if __name__ == "__main__":
    main()
