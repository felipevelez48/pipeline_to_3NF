"""
Para no tener dependencia de varias DAGs, vamos a realizar una sola con dos tareas:
    t1_ingest  -->  ingesta CSV → tabla jobs_raw
    t2_transform --> normaliza y carga modelo 3 NF
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys

# para que Airflow encuentre los scripts montados en /opt/airflow/scripts que contienen las tareas
sys.path.append("/opt/airflow/scripts")

from ingest_raw import main as ingest_raw_main
from transform_to_3nf import main as transform_3nf_main

default_args = {
    "owner": "Felipe Velez",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="jobs_ingest_transform",
    start_date=datetime(2025, 7, 1),
    schedule_interval=None,      # ejecución manual
    catchup=False,
    tags=["jobs", "etl"],
    default_args=default_args,
) as dag:

    # t1: ingesta CSV crudo hacia --> jobs_raw
    t1_ingest = PythonOperator(
        task_id="t1_ingest",
        python_callable=ingest_raw_main,
    )

    # t2: transforma la data para llevarla de modelo 3NF
    t2_transform = PythonOperator(
        task_id="t2_transform",
        python_callable=transform_3nf_main,
    )

    # dependencia
    t1_ingest >> t2_transform
