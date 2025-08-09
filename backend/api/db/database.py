import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("backend/db/stocks.db")

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def create_all_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Table: stock_metadata
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stock_metadata (
        symbol TEXT PRIMARY KEY,
        name TEXT,
        description TEXT,
        sector TEXT,
        industry TEXT,
        market_cap REAL,
        pe_ratio REAL,
        dividend_yield REAL,
        eps REAL,
        website TEXT,
        last_updated TIMESTAMP
    );
    """)

    # Table: stock_features
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stock_features (
        symbol TEXT PRIMARY KEY,
        close_price REAL,
        pe_ratio REAL,
        eps REAL,
        revenue_growth REAL,
        last_updated TIMESTAMP
    );
    """)

    # Table: valuation_data
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS valuation_data (
        symbol TEXT PRIMARY KEY,
        sentiment_score REAL,
        financial_score REAL,
        growth_score REAL,
        total_score REAL,
        verdict TEXT,
        contradiction TEXT,
        valuation_label TEXT,
        confidence REAL,
        last_updated TIMESTAMP
    );
    """)

    # Table: news_cache
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS news_cache (
        url TEXT PRIMARY KEY,
        content TEXT,
        sentiment REAL,
        domain TEXT,
        confidence REAL,
        timestamp TIMESTAMP
    );
    """)

    # Table: price_predictions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS price_predictions (
        symbol TEXT PRIMARY KEY,
        predicted_verdict TEXT,
        confidence REAL,
        model_inputs TEXT,
        last_updated TIMESTAMP
    );
    """)

    # Table: historical_prices
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historical_prices (
        symbol TEXT,
        date TEXT,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume INTEGER,
        PRIMARY KEY (symbol, date)
    );
    """)

    conn.commit()
    conn.close()
    print("✅ Tables created successfully.")


# ========================
# UPSERT HELPERS
# ========================

def upsert_stock_features(symbol, close_price, pe_ratio, eps, revenue_growth):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO stock_features (symbol, close_price, pe_ratio, eps, revenue_growth, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                close_price=excluded.close_price,
                pe_ratio=excluded.pe_ratio,
                eps=excluded.eps,
                revenue_growth=excluded.revenue_growth,
                last_updated=excluded.last_updated;
        """, (symbol, close_price, pe_ratio, eps, revenue_growth, datetime.utcnow()))
        conn.commit()

def upsert_valuation_data(symbol, sentiment_score, financial_score, growth_score, total_score,
                          verdict, eps_growth, revenue_growth, confidence, contradiction, valuation_label):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO valuation_data (
                symbol, sentiment_score, financial_score, growth_score, total_score,
                verdict, eps_growth, revenue_growth, confidence, contradiction, valuation_label, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                sentiment_score=excluded.sentiment_score,
                financial_score=excluded.financial_score,
                growth_score=excluded.growth_score,
                total_score=excluded.total_score,
                verdict=excluded.verdict,
                eps_growth=excluded.eps_growth,
                revenue_growth=excluded.revenue_growth,
                confidence=excluded.confidence,
                contradiction=excluded.contradiction,
                valuation_label=excluded.valuation_label,
                last_updated=excluded.last_updated;
        """, (
            symbol, sentiment_score, financial_score, growth_score, total_score,
            verdict, eps_growth, revenue_growth, confidence, contradiction, valuation_label, datetime.utcnow()
        ))
        conn.commit()

def upsert_news_cache(symbol, title, url, content, sentiment_score, impact_score, published_at):
    with get_connection() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO news_cache (
                symbol, title, url, content, sentiment_score, impact_score, published_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (
            symbol, title, url, content, sentiment_score, impact_score, published_at
        ))
        conn.commit()

# ========== Test ==========
if __name__ == "__main__":
    create_all_tables()