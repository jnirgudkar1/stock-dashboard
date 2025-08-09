import sqlite3
from pathlib import Path
from typing import Iterable, Mapping, Optional
from datetime import datetime

# Absolute path: backend/db/stocks.db
ABS_DB = (Path(__file__).resolve().parents[2] / "db" / "stocks.db").resolve()

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
            symbol TEXT, title TEXT, content TEXT,
            sentiment_score REAL, impact_score REAL,
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
        return datetime.strptime(r["lu"], "%Y-%m-%d %H:%M:%S")

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