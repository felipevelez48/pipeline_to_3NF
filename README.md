# Data Pipeline Micro‑Batches 📦 ➜ 3 NF ➜ Tests ➜ Airflow

![Pragma logo](images/pragma.jpg)

> **Reto técnico – Data Engineer**  
> Ingestamos un CSV masivo de ofertas de empleo, lo normalizamos en un modelo 3 NF en PostgreSQL y orquestamos el ciclo completo con Docker Compose + Airflow.  Incluimos pruebas de calidad con pytest & pandera y un diseño conceptual OLAP.

---

## 📂 Estructura del repositorio

```text
.
├── data/                    # ➊ CSV crudo (data_jobs.csv)
├── dags/
│   └── jobs_ingest_transform_dag.py
├── models/
│   └── schema.sql           # DDL 3 NF + índices
├── scripts/
│   ├── __init__.py
│   ├── ingest_raw.py        # carga data_jobs.csv → raw.jobs
│   └── transform_to_3nf.py  # limpieza + 3 NF
├── tests/
│   ├── test_schema_raw.py   # Pandera
│   ├── test_functions_cleaning.py
│   └── test_jobs_integrity.py
├── docker-compose.yml       # PostgreSQL 16 + Airflow 2.9
├── pyproject.toml           # Ruff config
├── requirements.txt         # libs extra (ftfy, pandera…)
└── README.md                # ← estás aquí
```


## ⚙️ Requisitos

- Docker & Docker Compose v2

- Make (opcional) para atajos (make up, make test, …)

- No necesitas instalar nada en tu máquina: todo corre en contenedores.

## 🚀 Puesta en marcha rápida
```bash
# 1) Copia variables de ejemplo y ajusta si quieres
cp .env.example .env.engineer

# 2) Construye imágenes e inicia servicios (≈3‑4 min la 1ª vez)
docker compose up -d --build

# 3) Abre Airflow UI → http://localhost:8080  (admin / admin)
#    Lanza la DAG jobs_ingest_transform (t1_ingest → t2_transform)

# 4) Ejecuta pruebas de calidad
docker compose exec airflow pytest -q
# 8 tests OK  ✅
```

## 🗄️ Modelo relacional (3 NF)
```bash
companies 1─┐
locations 1─┤
job_titles 1┤
schedules 1─┴─┐
salary_rates 1┘ │
                │   (M:N)  skills
        jobs───────────────┬────────── job_skill

```
- Columnas FK ahora son INTEGER y todas las claves foráneas se crearon (ver schema.sql).

- Índices extra en jobs(location_id) y jobs(company_id) aceleran las JOINs.

## 🧪 Tests con pytest + pandera

| Test                             | Qué valida                                              |
| -------------------------------- | ------------------------------------------------------- |
| **test\_schema\_raw\.py**        | El DF crudo respeta tipos y nulos.                      |
| **test\_functions\_cleaning.py** | Unit tests de `fix_encoding`, `clean_location`, etc.    |
| **test\_jobs\_integrity.py**     | *Checks* de FK + conteo de huérfanos (ahora todo pasa). |

## 🔄 Orquestación (Airflow)

- DAG: dags/jobs_ingest_transform_dag.py

    - t1_ingest → lee CSV y llena raw.jobs (micro‑batches vía chunksize=1000).

    - t2_transform → normaliza y carga 3 NF (también en lotes).

- Health‑check PostgreSQL con pg_isready evita carreras de arranque.

- Logs montados en ./logs para fácil inspección.

## 🌟 Diseño Estrella (conceptual)

| Componente                  | Descripción                                                     |
| --------------------------- | --------------------------------------------------------------- |
| **Fact** `fact_job_posting` | Grano: 1 oferta. FK: company, title, location, date.            |
| Dim empresa                 | sector, tamaño, HQ.                                             |
| Dim ubicación               | ciudad, estado, país, lat/long.                                 |
| Dim fecha                   | día, mes, Q, festivo.                                           |
| Dim título                  | familia (Data Engineer, Analyst…).                              |
| Dim skill\*                 | con puente `fact_job_skill` para análisis de skills.            |
| **Medidas**                 | `salary_year_avg`, `salary_hour_avg`, `is_remote`, `days_open`. |

## 📝 Decisiones de diseño

- Micro‑batches con chunksize=1000 evitan OOM en portátiles de 8‑16 GB (dataset ~780 k rows).

- ftfy corrige mojibake UTF‑8/latin‑1 (“ROCKENÂ®” → “ROCKEN®”).

- PIP_ADDITIONAL_REQUIREMENTS agiliza prototipos; para producción se construiría imagen propia.

- Ruff elegido por rendimiento (≈10× Flake8).

- Pandera permite contratos de datos declarativos en puro Python.

- No se hardcodean credenciales; .env.engineer se monta vía env_file:.

## 💭 Retos & aprendizajes

- **Tipado flotante accidental** – pandas.to_sql convertía ids a float; los tests de FK fallaron y obligaron a castear a INTEGER.

- **Zombie tasks** – Airflow marcaba tareas como “zombie” por timeouts al procesar 12 M rows; chunking y method="multi" lo resolvieron.

- **Memoria** – El DataFrame completo no cabe; procesar en streaming fue clave.

- **Test first** – Ver el rojo de pytest me guio paso a paso hasta la base limpia.

- **Historia personal** – Descubrí lo fácil que es sobreestimar la RAM de un portátil; la ejecución fallaba a la mitad y aprendí a dejar de sobreestimar la memoria RAM, la solución fue realizar chunks más pequeños que el equipo pudiera soportar.

## ▶️ Cómo probar otra carga
```bash
# 1. Copia otro CSV grande a data/ y renombra el anterior si no quieres duplicar.
# 2. Lanza nuevamente la DAG desde la UI o por CLI:
docker compose exec airflow airflow dags trigger jobs_ingest_transform
# 3. Re‑ejecuta tests:
docker compose exec airflow pytest -q
```



## 📊🤖 Autor: John Felipe Vélez

### Data Engineer

