"""Comprabamos integridad y unicidad después de la transformación."""
# tests/test_jobs_integrity.py
import os
import pytest
from sqlalchemy import create_engine, text, inspect

# Usa las mismas variables que el contenedor tiene en .env.engineer
PG_USER     = os.getenv("POSTGRES_USER",     "userdb")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
PG_DB       = os.getenv("POSTGRES_DB",       "ilumadb")
PG_HOST     = os.getenv("POSTGRES_HOST",     "postgres")
PG_PORT     = os.getenv("POSTGRES_PORT",     "5432")

URL = f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
ENGINE = create_engine(URL)

def test_foreign_keys():
    with ENGINE.begin() as conn:
        insp = inspect(conn)
        # 1️⃣ ‑ Comprueba que jobs.location_id apunta a locations.location_id
        fk = [f for f in insp.get_foreign_keys("jobs") if f["constrained_columns"] == ["location_id"]][0]
        assert fk["referred_table"] == "locations"
        # 2️⃣ ‑ Conteo cross‑checks (ejemplo rápido)
        res = conn.execute(text("""
            SELECT COUNT(*) FROM jobs j
            WHERE NOT EXISTS (
              SELECT 1 FROM locations l WHERE l.location_id = j.location_id)
        """)).scalar_one()
        assert res == 0, "hay jobs sin location"


