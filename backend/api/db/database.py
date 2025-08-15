import sqlite3
from pathlib import Path
from typing import Iterable, Mapping, Optional
from datetime import datetime

# Absolute path: backend/db/stocks.db
ABS_DB = (Path(__file__).resolve().parents[2] / "db" / "stocks.db").resolve()
print(f"[DB] Using SQLite at: {ABS_DB}")
def get_connection():
    ABS_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(ABS_DB), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn

def create_all_tables():
    with get_connection() as conn:
        cur = conn.cursor()

        # --- tables (create-if-missing) ---
        cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_metadata(
            symbol TEXT PRIMARY KEY,
            name TEXT, description TEXT, sector TEXT, industry TEXT, website TEXT,
            marketCap REAL, peRatio REAL, dividendYield REAL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS historical_prices(
            symbol TEXT NOT NULL,
            date   TEXT NOT NULL,
            open REAL, high REAL, low REAL, close REAL, volume INTEGER,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(symbol, date)
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS news_cache(
            url TEXT PRIMARY KEY,
            -- some older DBs may be missing symbol/published_at/last_updated
            symbol TEXT,
            title TEXT,
            content TEXT,
            sentiment_score REAL,
            impact_score REAL,
            published_at TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_features(
            symbol TEXT PRIMARY KEY,
            close_price REAL, pe_ratio REAL, eps REAL, revenue_growth REAL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS valuation_data(
            symbol TEXT PRIMARY KEY,
            sentiment_score REAL, financial_score REAL, growth_score REAL,
            total_score REAL, verdict TEXT,
            eps_growth REAL, revenue_growth REAL, confidence REAL,
            contradiction TEXT, valuation_label TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS price_predictions(
            symbol TEXT PRIMARY KEY,
            prob_up REAL, prob_down REAL, label TEXT,
            model_loaded_at REAL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # --- lightweight migrations for existing DBs ---
        def table_columns(table: str) -> set[str]:
            # Can't param table name with ?; build carefully
            rows = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
            return {r["name"] if isinstance(r, sqlite3.Row) else r[1] for r in rows}

        def ensure_column(table: str, col: str, decl: str):
            cols = table_columns(table)
            if col not in cols:
                conn.execute(f'ALTER TABLE "{table}" ADD COLUMN {col} {decl};')

        # Ensure new-ish columns on news_cache
        ensure_column("news_cache", "symbol", "TEXT")
        ensure_column("news_cache", "published_at", "TEXT")
        ensure_column("news_cache", "last_updated", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

        # --- indexes (only if columns exist) ---
        def has_cols(table: str, want: list[str]) -> bool:
            cols = table_columns(table)
            return all(c in cols for c in want)

        cur.execute("CREATE INDEX IF NOT EXISTS idx_hist_symbol_date ON historical_prices(symbol, date);")

        if has_cols("news_cache", ["symbol", "published_at"]):
            cur.execute("CREATE INDEX IF NOT EXISTS idx_news_symbol_published ON news_cache(symbol, published_at);")

        conn.commit()

# ------------- Cache helpers -------------
def db_upsert_metadata(row: Mapping):
    cols = ("symbol","name","description","sector","industry","website","marketCap","peRatio","dividendYield")
    vals = [row.get(c) for c in cols]
    placeholders = ",".join(["?"]*len(cols))
    updates = ",".join([f"{c}=excluded.{c}" for c in cols[1:]])
    sql = f"""
      INSERT INTO stock_metadata({",".join(cols)}) VALUES({placeholders})
      ON CONFLICT(symbol) DO UPDATE SET {updates}, last_updated=CURRENT_TIMESTAMP
    """
    with get_connection() as conn:
        conn.execute(sql, vals)
        conn.commit()

def db_get_metadata(symbol: str) -> Optional[dict]:
    with get_connection() as conn:
        cur = conn.execute("SELECT * FROM stock_metadata WHERE symbol=?", (symbol,))
        r = cur.fetchone()
        return dict(r) if r else None

def db_upsert_prices(rows: Iterable[Mapping]):
    rows = list(rows or [])
    if not rows:
        return
    sql = """
      INSERT INTO historical_prices(symbol,date,open,high,low,close,volume)
      VALUES(?,?,?,?,?,?,?)
      ON CONFLICT(symbol,date) DO UPDATE SET
        open=excluded.open, high=excluded.high, low=excluded.low,
        close=excluded.close, volume=excluded.volume,
        last_updated=CURRENT_TIMESTAMP
    """
    with get_connection() as conn:
        conn.executemany(sql, [
            (r["symbol"], r["date"], r.get("open"), r.get("high"),
             r.get("low"), r.get("close"), r.get("volume"))
            for r in rows
        ])
        conn.commit()

def db_get_prices(symbol: str, limit: int = 500) -> list[dict]:
    with get_connection() as conn:
        cur = conn.execute("""
          SELECT * FROM historical_prices
          WHERE symbol=?
          ORDER BY date DESC
          LIMIT ?
        """, (symbol, limit))
        return [dict(x) for x in cur.fetchall()]

def db_get_prices_last_updated(symbol: str) -> Optional[datetime]:
    with get_connection() as conn:
        r = conn.execute("""
          SELECT MAX(last_updated) AS lu
          FROM historical_prices
          WHERE symbol=?
        """, (symbol,)).fetchone()
        if not r or not r["lu"]:
            return None
        lu = str(r["lu"])
        # Try std, then ISO
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
            try:
                return datetime.strptime(lu, fmt)
            except ValueError:
                pass
        try:
            return datetime.fromisoformat(lu)
        except Exception:
            return None

def db_get_stock_features(symbol: str) -> dict | None:
    with get_connection() as conn:
        r = conn.execute(
            "SELECT symbol, close_price, pe_ratio, eps, revenue_growth, last_updated "
            "FROM stock_features WHERE symbol=?",
            (symbol,),
        ).fetchone()
        return dict(r) if r else None

def db_upsert_stock_features(row: dict) -> None:
    cols = ("symbol", "close_price", "pe_ratio", "eps", "revenue_growth")
    vals = [row.get(c) for c in cols]
    placeholders = ",".join(["?"] * len(cols))
    updates = ",".join([f"{c}=excluded.{c}" for c in cols[1:]])
    sql = f"""
      INSERT INTO stock_features({",".join(cols)}) VALUES({placeholders})
      ON CONFLICT(symbol) DO UPDATE SET {updates}, last_updated=CURRENT_TIMESTAMP
    """
    with get_connection() as conn:
        conn.execute(sql, vals)
        conn.commit()

if __name__ == "__main__":
    print(f"[DB] Using SQLite at: {ABS_DB}")
    create_all_tables()
    print("[DB] Tables created.")

    # --- dynamic import of backend/scripts/preload_data.py ---
    from pathlib import Path
    import importlib.util, sys

    SCRIPTS_FILE = Path(__file__).resolve().parents[2] / "scripts" / "preload_data.py"
    preload_data = None
    if SCRIPTS_FILE.exists():
        spec = importlib.util.spec_from_file_location("preload_data", str(SCRIPTS_FILE))
        preload_data = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(preload_data)
    else:
        print(f"[DB] preload_data.py not found at: {SCRIPTS_FILE}")

    # Your ticker list
    TICKERS = ["AAPL", "MSFT", "GOOGL", "RKLB", "BKSY", "TSLA", "AMZN"]

    # Try to import preloader logic
    try:
        from backend.scripts import preload_data
    except ImportError:
        try:
            # fallback if run from within backend/
            import scripts.preload_data as preload_data
        except ImportError as e:
            print("[DB] Could not import preload_data:", e)
            preload_data = None

    if preload_data:
        for sym in TICKERS:
            try:
                preload_data.preload_symbol(
                    sym,
                    force=True,               # always refresh when run manually
                    full_history=True,        # get full history
                    prices_ttl=0,
                    metadata_ttl=0,
                    news_limit=25
                )
            except Exception as e:
                print(f"[ERROR] Failed to preload {sym}: {e}")

    # Show resulting tables
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """).fetchall()
        print("[DB] Tables in database:")
        for r in rows:
            print(" -", r[0])