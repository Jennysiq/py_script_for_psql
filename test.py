#!/usr/bin/env python3
import os, time, base64, gzip, subprocess, sys
import requests
import psycopg
from dotenv import load_dotenv

load_dotenv()

#default vars

TOKEN        = os.getenv("TOKEN", "").strip()
PG_PORT      = os.getenv("PG_PORT", "5433")
PG_DB        = os.getenv("PG_DB", "ctfdb")
PG_PASS      = os.getenv("PG_PASSWORD", "pg")
PG_USER      = os.getenv("PG_USER", "postgres")
PG_CONT      = os.getenv("PG_CONTAINER", "hackattic-pg")
PG_IMAGE     = os.getenv("PG_IMAGE", "postgres:16")

if not TOKEN:
    print("ERROR: set TOKEN in env or .env.example", file=sys.stderr)
    sys.exit(1)

#URLS

PROBLEM_URL  = f"https://hackattic.com/challenges/backup_restore/problem?access_token={TOKEN}"
SOLVE_URL    = f"https://hackattic.com/challenges/backup_restore/solve?access_token={TOKEN}"
DSN          = f"postgresql://{PG_USER}:{PG_PASS}@localhost:{PG_PORT}/{PG_DB}"

def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)

#docker run psql

def ensure_postgres():
    subprocess.run(["docker","rm","-f",PG_CONT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sh(["docker","run","-d","--name",PG_CONT,
        "-e", f"POSTGRES_PASSWORD={PG_PASS}",
        "-p", f"{PG_PORT}:5432", PG_IMAGE],
       stdout=subprocess.DEVNULL)
    for _ in range(90):
        ok = subprocess.run(["docker","exec",PG_CONT,"pg_isready","-U",PG_USER],
                            stdout=subprocess.DEVNULL).returncode == 0
        if ok: break
        time.sleep(1)
    else:
        raise RuntimeError("Postgres not ready")
    sh(["docker","exec",PG_CONT,"createdb","-U",PG_USER,PG_DB])

#decompress

def fetch_dump_sql() -> str:
    r = requests.get(PROBLEM_URL, timeout=30)
    r.raise_for_status()
    b64 = r.json()["dump"]
    raw = base64.b64decode(b64)
    try:
        raw = gzip.decompress(raw)
    except OSError:
        pass
    return raw.decode("utf-8", "replace")

#restoring dump

def restore_via_psql(sql_text: str):
    subprocess.run(
        ["docker","exec","-i",PG_CONT,"psql","-U",PG_USER,"-d",PG_DB],
        input=sql_text.encode(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
    )

#checking alive sns

def query_alive_ssns() -> list[str]:
    with psycopg.connect(DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT ssn
                FROM public.criminal_records
                WHERE lower(btrim(status)) = 'alive'
                ORDER BY ssn
            """)
            return [r[0] for r in cur.fetchall()]

#print and sent

def main():
    ensure_postgres()
    sql_text = fetch_dump_sql()
    restore_via_psql(sql_text)
    ssns = query_alive_ssns()
    print("Alive SSNs:")
    for s in ssns:
        print(" ", s)

    import json
    payload = {"alive_ssns": ssns}
    resp = requests.post(SOLVE_URL, json=payload, timeout=30)
    print("Solve status:", resp.status_code)
    print("Solve body  :", resp.text)

    subprocess.run(["docker","rm","-f",PG_CONT]) #remove-docker

#output

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("[ERROR]", e, file=sys.stderr)
        sys.exit(1)
