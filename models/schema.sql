/* -----------------------------------------------------------
  -- companies --> Hacemos una fila por empresa. Catálogos simples
   -----------------------------------------------------------*/
CREATE TABLE companies (
    company_id   SERIAL PRIMARY KEY,
    name         TEXT NOT NULL UNIQUE
);

-- job titles --> Nombres estandarizados
CREATE TABLE job_titles (
    job_title_id SERIAL PRIMARY KEY,
    title_short  TEXT NOT NULL UNIQUE,
    title_full   TEXT
);

-- locations --> Ubicación de la oferta de trabajo(por ciudad, estado, país)
CREATE TABLE locations (
    location_id  SERIAL PRIMARY KEY,
    raw_location TEXT NOT NULL UNIQUE,   -- «Ciudad, País» sin normalizar
    city         TEXT,
    state        TEXT,
    country      TEXT
);

-- schedule --> Tipos de jornada
CREATE TABLE schedules (
    schedule_id   SERIAL PRIMARY KEY,
    schedule_type TEXT NOT NULL UNIQUE   -- p.ej. Full‑Time, Part‑Time…
);

-- salary_rates --> Miramos si es por año o por hora
CREATE TABLE salary_rates (
    rate_id   SERIAL PRIMARY KEY,
    rate_name TEXT NOT NULL UNIQUE       -- Hour, Year, …
);

/* -----------------------------------------------------------
   -- jobs --> oferta principal
   -----------------------------------------------------------*/
CREATE TABLE jobs (
    job_id            SERIAL PRIMARY KEY,

    company_id        INT NOT NULL,
    job_title_id      INT NOT NULL,
    location_id       INT NOT NULL,
    schedule_id       INT,
    rate_id           INT,

    via               TEXT,
    work_from_home    BOOLEAN,
    posted_at         TIMESTAMP,
    search_location   TEXT,
    salary_year_avg   NUMERIC,
    salary_hour_avg   NUMERIC,
    no_degree         BOOLEAN,
    health_insurance  BOOLEAN,
    skill_groups      JSONB,

    /* --- claves foráneas nombradas --- */
    CONSTRAINT fk_jobs_company
        FOREIGN KEY (company_id)   REFERENCES companies(company_id),
    CONSTRAINT fk_jobs_title
        FOREIGN KEY (job_title_id) REFERENCES job_titles(job_title_id),
    CONSTRAINT fk_jobs_location
        FOREIGN KEY (location_id)  REFERENCES locations(location_id),
    CONSTRAINT fk_jobs_schedule
        FOREIGN KEY (schedule_id)  REFERENCES schedules(schedule_id),
    CONSTRAINT fk_jobs_rate
        FOREIGN KEY (rate_id)      REFERENCES salary_rates(rate_id)
);

/* -----------------------------------------------------------
   -- skills --> Lista única de habilidades
   -----------------------------------------------------------*/
CREATE TABLE skills (
    skill_id   SERIAL PRIMARY KEY,
    skill_name TEXT NOT NULL UNIQUE
);

--job_skill --> tabla puente entre jobs y skills para resolver el problema de muchos a muchos
CREATE TABLE job_skill (
    job_id   INT NOT NULL,
    skill_id INT NOT NULL,
    PRIMARY KEY (job_id, skill_id),

    CONSTRAINT fk_job_skill_job
        FOREIGN KEY (job_id)   REFERENCES jobs(job_id)     ON DELETE CASCADE,
    CONSTRAINT fk_job_skill_skill
        FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE
);

/* -----------------------------------------------------------
   --Creamos indices para mejorar consultas
   -----------------------------------------------------------*/
CREATE INDEX idx_jobs_posted_at ON jobs(posted_at);
CREATE INDEX idx_jobs_company   ON jobs(company_id);
CREATE INDEX idx_jobs_location  ON jobs(location_id);

