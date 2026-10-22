import os, sqlite3
from contextlib import contextmanager
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; SQLITE_FILE=ROOT/"data"/"yelen.db"; DATABASE_URL=os.environ.get("YELEN_DATABASE_URL","")
def using_postgres(): return DATABASE_URL.startswith(("postgresql://","postgres://"))
@contextmanager
def connection():
    if using_postgres():
        import psycopg; conn=psycopg.connect(DATABASE_URL)
    else:
        SQLITE_FILE.parent.mkdir(parents=True,exist_ok=True); conn=sqlite3.connect(SQLITE_FILE); conn.row_factory=sqlite3.Row
    try: yield conn; conn.commit()
    finally: conn.close()
def initialize():
    key="BIGSERIAL PRIMARY KEY" if using_postgres() else "INTEGER PRIMARY KEY AUTOINCREMENT"
    with connection() as conn: conn.execute(f"CREATE TABLE IF NOT EXISTS reports (id {key},district TEXT NOT NULL,community TEXT NOT NULL,latitude REAL NOT NULL,longitude REAL NOT NULL,power_status TEXT NOT NULL,reported_at TEXT NOT NULL,confidence REAL NOT NULL DEFAULT 0,likely_outage INTEGER NOT NULL DEFAULT 0,cluster_size INTEGER NOT NULL DEFAULT 1)")
def placeholder(): return "%s" if using_postgres() else "?"
def rows_to_dicts(cursor):
    rows=cursor.fetchall()
    if not rows:return []
    if isinstance(rows[0],sqlite3.Row):return [dict(r) for r in rows]
    columns=[d.name for d in cursor.description]; return [dict(zip(columns,r)) for r in rows]
