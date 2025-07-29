# Data Pipeline Micro‑Batches 📦 ➜ 3 NF ➜ Tests ➜ Airflow

> **Reto técnico – Data Engineer**  
> Ingesta de un un CSV masivo de ofertas de empleo, lo normalizamos en un modelo 3 NF en PostgreSQL y orquestamos el ciclo completo con Docker Compose + Airflow.  Incluí pruebas de calidad con pytest & pandera y un diseño conceptual OLAP.

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

- Índices extra en jobs(location_id) y jobs(company_id) aceleran los JOINs.

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

## 📝 Decisiones de diseño — ¿por qué así y no de otra forma?

| Capa                     | Elección                                                | ¿Por qué la elegimos?                                                                                                                                                                                                                                                   | Alternativas consideradas                                                                                             |
| ------------------------ | ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **Base de datos OLTP**   | **PostgreSQL 16 Alpine**                                | - **Estándar de‑facto** en la comunidad de datos, 100 % open‑source.<br>- Soporta JSONB, índices GIN y funciones avanzadas que facilitan prototipar sin inventar “data lakes” caseros.<br>- Imagen *Alpine* → \~ 70 MB; arranca en segundos y cabe en equipos modestos. | MySQL/MariaDB (sin JSONB nativo), SQLite (monousuario), Cloud‑DB (costo y credenciales)                               |
| **Orquestador**          | **Apache Airflow 2.9**                                  | - Necesitábamos *scheduler*, *retries*, logs y UI; Airflow los trae *out‑of‑the‑box*.<br>- DAGs como código → versionables en Git.<br>- Gran comunidad, fácil escalar de docker‑compose → K8s si el proyecto crece.                                                     | Prefect (muy bueno pero lock‑in licencias), Dagster (curva de aprendizaje + GraphQL), Cron + Bash (pobre visibilidad) |
| **Formato de ingestión** | **CSV plano** → tabla `raw.jobs`                        | - Es el formato original del reto.<br>- Pandas carga \~200 MB en < 5 s dentro del contenedor; no valía complicarse con Parquet.                                                                                                                                         | Parquet/Avro (útil para particiones, pero overkill en demo)                                                           |
| **Modelo lógico**        | **3NF + catálogos** (`companies`, `locations`, `jobs`…) | - Desnormalizar todo en una sola tabla produce duplicación masiva (10 M+ filas × columnas repetidas).<br>- 3NF reduce tamaño \~3× y protege integridad con FK.<br>- Facilita construir *Star Schema* después (dimensiones ya están).                                    | “One Big Table”, esquema ancho (simple al inicio pero caro y propenso a errores)                                      |
| **Tests de calidad**     | **pytest + Pandera**                                    | - pytest → framework de facto, compatible con GitHub Actions.<br>- Pandera describe *dataframes* como *schemas* declarativos; perfecta para validar DF intermedios y simular “dbt test” sin dbt.<br>- Se integra con pytest (`@pa.check_types`).                        | Great Expectations (potente pero pesado), dbt test (requiere dbt DAG extra), asserts manuales                         |
| **Estilo & Lint**        | **ruff**                                                | - Lint + format en \~50× la velocidad de flake8/black; una sola herramienta.<br>- Se ejecuta en CI en < 5 s.                                                                                                                                                            | flake8 + black + isort (tres pasos), pylint (lento)                                                                   |
| **Containerización**     | **docker‑compose**                                      | - Un solo comando levanta Postgres + Airflow; ideal para revisores.<br>- `_PIP_ADDITIONAL_REQUIREMENTS` instala libs sin construir imagen custom → menos fricción al probar.                                                                                            | Build de imagen propia (más limpio en prod), makefile local                                                           |
| **Gestión de secretos**  | **`.env.engineer` + variables Docker**                  | - Nada de credenciales hardcodeadas; los valores reales se inyectan en tiempo de arranque.<br>- Compatible con GitHub Secrets si se deploya en Actions.                                                                                                                 | Docker Secrets, HashiCorp Vault (innecesario en demo)                                                                 |


## 💭🧠 Retos, decisiones & aprendizajes

- **RAM vs. micro‑batches**
    -Procesar ~800 k filas y 12 M registros puente en un portátil de 8 GB demostró que cargar todo en memoria no escala. Opté por chunksize=1 000 y method="multi" en pandas.to_sql, para enviar lotes pequeños a Postgres sin reventar la RAM.

- **Tipado flotante accidental**
    - Al volcar DataFrames, to_sql convertía las claves foráneas a double precision. Los tests de integridad fallaron. Solución: castear con ALTER TABLE … ALTER COLUMN … TYPE integer USING …::integer antes de crear las FK, y añadir un test Pandera que confirme dtype == Int64.

- **Orden correcto: índices y FK**
    - Si creas las FK cuando las columnas aún son floats, luego no puedes castear. El flujo ganador fue: castear ➜ limpiar nulos ➜ crear índices ➜ agregar claves foráneas.

- **Zombie tasks en Airflow**
    - El scheduler marcaba la tarea de transformación como zombie porque insertar millones de filas excedía el timeout. Al fragmentar la carga con micro‑batches y reducir la concurrencia de la DAG, el run se estabilizó (cada lote < 60 s).

- **Memoria subestimada**
    -Asumí que el CSV de 220 MB cabía holgado… y no. Ver la máquina intercambiando swap enseñó que el “demo laptop” no es la referencia; diseña para que el pipeline (no tu RAM) escale.

- **Git y archivos grandes**
    -Subir ese CSV despertó el limite de 100 MB de GitHub. Tuve que aprender git filter‑repo, purgar el historial y rehacer el commit. Moraleja: agrega los datos crudos a .gitignore desde el día 0 — o usa Git LFS si realmente los necesitas versionados.

- **Airflow local ≠ Producción**
    - _PIP_ADDITIONAL_REQUIREMENTS es práctico para probar dependencias extra (ftfy, ruff, Pandera) pero reinstala paquetes en cada docker up, lo cual es frágil y lento. En producción se reemplazaría por una imagen custom y versionada.

- **Pandera frente a dbt**
    -Elegí Pandera porque nuestras transformaciones viven en Python y queríamos validar DataFrames antes de llegar a la base. Si la arquitectura migrara a Spark + Parquet, lo razonable sería mover las pruebas de calidad a dbt Core.

- **Autovacuum y performance**
    - Durante la ingesta masiva noté que autovacuum de Postgres se activaba y alargaba la DAG. En un entorno real, ajustaríamos maintenance_work_mem y autovacuum_naptime, y crearíamos los índices después de la carga inicial.

- **Test‑first mindset**
    - Mantener pytest en rojo hasta que cada falla se resuelva guía el desarrollo. Todos los tests corren en < 10 s, de modo que iterar es rápido y seguro.

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

