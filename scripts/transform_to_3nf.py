import os, json, re, logging
import pandas as pd
from sqlalchemy import create_engine, text
import ftfy

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s: %(message)s")

ENGINE = create_engine(os.getenv("AIRFLOW__DATABASE__SQL_ALCHEMY_CONN"))

# ---------- helpers de limpieza ----------
fix_encoding     = lambda t: t if pd.isna(t) else ftfy.fix_text(t)
clean_location   = lambda r: ("Remote" if str(r).strip().lower()=="anywhere"
                              else re.sub(r"\s*\(\+\d+\s+others\)","",fix_encoding(r)).strip()
                              ) if not pd.isna(r) else r
SCHEDULE_MAP = {"full":"Full-Time","part":"Part-Time","intern":"Internship",
                "contract":"Contract","temp":"Temp"}
def clean_schedule(v):
    if pd.isna(v): return v
    v=v.lower()
    return next((std for k,std in SCHEDULE_MAP.items() if k in v),"Other")

def upsert_cat(df, table, col_src, col_dst="name", id_col=None):
    id_col = id_col or f"{table.rstrip('s')}_id"
    vals = df[col_src].dropna().unique().tolist()
    if not vals: return {}
    with ENGINE.begin() as conn:
        conn.execute(
            text(f"INSERT INTO {table} ({col_dst}) "
                 f"SELECT unnest(:vals) ON CONFLICT ({col_dst}) DO NOTHING"),
            {"vals": vals},
        )
        rows = conn.execute(
            text(f"SELECT {col_dst}, {id_col} FROM {table} "
                 f"WHERE {col_dst}=ANY(:vals)"), {"vals": vals}).fetchall()
    return {r[0]: r[1] for r in rows}

# ---------- procesamiento incremental ----------
CHUNK = 50_000          # filas a la vez   (ajusta si ves OOM de nuevo)

def process_chunk(df, first_jobs_insert):
    # --- limpiezas ---
    df = (df.rename(columns={"job_via":"via","job_work_from_home":"work_from_home"})
            .assign(posted_at    =pd.to_datetime(df["job_posted_date"]),
                    via          =lambda x: x.via.map(fix_encoding),
                    work_from_home =lambda x: x.work_from_home.fillna(False),
                    company_name =lambda x: x.company_name.map(fix_encoding),
                    job_location =lambda x: x.job_location.map(clean_location),
                    job_schedule_type=lambda x: x.job_schedule_type.map(clean_schedule),
                    job_skills  =lambda x: x.job_skills.apply(
                                        lambda lst: list(dict.fromkeys(lst)) if lst else lst)
                   )
          )

    # --- catálogos (basados solo en chunk) ---
    map_company  = upsert_cat(df,"companies","company_name",id_col="company_id")
    map_location = upsert_cat(df,"locations","job_location",
                              "raw_location",id_col="location_id")
    map_title    = upsert_cat(df,"job_titles","job_title_short",
                              "title_short",id_col="job_title_id")
    map_sched    = upsert_cat(df,"schedules","job_schedule_type",
                              "schedule_type",id_col="schedule_id")
    map_rate     = upsert_cat(df,"salary_rates","salary_rate",
                              "rate_name",id_col="rate_id")

    jobs_cols = ["via","work_from_home","posted_at","search_location",
                 "salary_year_avg","salary_hour_avg",
                 "job_no_degree_mention","job_health_insurance"]
    jobs_df = df.assign(
            company_id   =lambda x: x.company_name.map(map_company),
            job_title_id =lambda x: x.job_title_short.map(map_title),
            location_id  =lambda x: x.job_location.map(map_location),
            schedule_id  =lambda x: x.job_schedule_type.map(map_sched),
            rate_id      =lambda x: x.salary_rate.map(map_rate),
            skill_groups =lambda x: x.job_type_skills.apply(json.dumps)
        )[jobs_cols+["company_id","job_title_id","location_id","schedule_id","rate_id"]]

    with ENGINE.begin() as conn:
        jobs_df.to_sql("jobs", conn,
                       if_exists="replace" if first_jobs_insert else "append",
                       index=False, chunksize=1_000, method="multi")
        if first_jobs_insert:
            # crea PK solo la primera vez
            conn.execute(text("ALTER TABLE jobs ADD COLUMN job_id SERIAL PRIMARY KEY"))

        # ids recién insertados
        inserted = len(jobs_df)
        last_id  = conn.execute(text("SELECT currval('jobs_job_id_seq')")).scalar()
        job_ids  = range(last_id - inserted + 1, last_id + 1)

        # skills y puente
        skills_series = df.job_skills.explode().dropna().str.strip()
        skills_map = upsert_cat(pd.DataFrame({"skill": skills_series}),
                                "skills","skill","skill_name",id_col="skill_id")

        link_rows = [{"job_id":j,"skill_id":skills_map.get(sk.strip())}
                     for j,skills in zip(job_ids, df.job_skills)
                     for sk in (skills or []) if skills_map.get(sk.strip())]

        if link_rows:
            pd.DataFrame(link_rows).drop_duplicates().to_sql(
                "job_skill", conn, if_exists="append",
                index=False, chunksize=1_000
            )

def main():
    first = True
    for chunk in pd.read_sql("SELECT * FROM jobs_raw", ENGINE,
                             chunksize=CHUNK):
        logging.info("Procesando %d filas …", len(chunk))
        process_chunk(chunk, first_jobs_insert=first)
        first = False
    logging.info("✨ Transformación terminada sin OOM ✨")

if __name__ == "__main__":
    main()

