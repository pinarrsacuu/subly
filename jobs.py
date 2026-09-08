"""
Video isleme isini arka planda (async) yurutmek icin kullanilan is (job) kaydi.
Islem bir thread icinde calisir, durumu Postgres'teki jobs tablosunda tutulur -
boylece kullanici HTTP istegini bekletmeden "isleniyor" sayfasina yonlendirilip
durumu kontrol edebilir (Cloudflare/gunicorn'un uzun istekleri kesme riskini ortadan kaldirir).
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

import psycopg2

from usage_tracker import DATABASE_URL


def _connect():
    return psycopg2.connect(DATABASE_URL)


def init_jobs_db() -> None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'queued',
                    output_filename TEXT,
                    error_title TEXT,
                    error_body TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            """)
        conn.commit()


def create_job(email: str) -> str:
    job_id = uuid.uuid4().hex
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO jobs (id, email, status) VALUES (%s, %s, 'queued')",
                (job_id, email.lower()),
            )
        conn.commit()
    return job_id


def get_job(job_id: str) -> Optional[dict]:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, email, status, output_filename, error_title, error_body FROM jobs WHERE id = %s",
                (job_id,),
            )
            row = cur.fetchone()
    if not row:
        return None
    return {
        "id": row[0], "email": row[1], "status": row[2],
        "output_filename": row[3], "error_title": row[4], "error_body": row[5],
    }


def mark_processing(job_id: str) -> None:
    _update(job_id, status="processing")


def mark_done(job_id: str, output_filename: str) -> None:
    _update(job_id, status="done", output_filename=output_filename)


def mark_error(job_id: str, error_title: str, error_body: str) -> None:
    _update(job_id, status="error", error_title=error_title, error_body=error_body)


def _update(job_id: str, **fields) -> None:
    fields["updated_at"] = datetime.now(timezone.utc)
    columns = ", ".join(f"{key} = %s" for key in fields)
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(f"UPDATE jobs SET {columns} WHERE id = %s", (*fields.values(), job_id))
        conn.commit()
