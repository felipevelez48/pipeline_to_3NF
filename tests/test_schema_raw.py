"""
Valida que el DataFrame obtenido de raw.jobs cumple con el contrato esperado.
Asumimos que la variable ENGINE está disponible (sqlalchemy.create_engine)
y apunta a la misma BD usada por Airflow.
"""
import pandas as pd
import pandera as pa
from pandera import Column, DataFrameSchema, Check

RAW_SCHEMA = DataFrameSchema(
    {
        "job_title_short"    : Column(str, nullable=False),
        "job_location"       : Column(str, nullable=True),
        "job_via"            : Column(str, nullable=True),
        "job_schedule_type"  : Column(str, nullable=True),
        "job_work_from_home" : Column(bool, nullable=True),
        "job_posted_date"    : Column(str, Check.str_matches(r"\d{4}-\d{2}-\d{2}"), nullable=False),
        "company_name"       : Column(str, nullable=True),
        # …añade las columnas que necesites
    },
    strict=False,          # permite columnas extras
)

def test_raw_csv_schema():
    df = pd.read_csv("data/data_jobs.csv")     # ruta relativa
    RAW_SCHEMA.validate(df.sample(1000, random_state=0))  # valida 1 000 filas
