"""
PostgreSQL connection pool with proper logging.
"""
import psycopg2
from psycopg2 import pool
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

# ── Connection Pool ─────────────────────────────────────────────
db_pool = None

try:
    db_pool = psycopg2.pool.SimpleConnectionPool(
        1, 10,  # min and max connections
        dsn=settings.DATABASE_URL,
    )
    if db_pool:
        logger.info("✅ PostgreSQL connected successfully — pool created")
except (Exception, psycopg2.DatabaseError) as error:
    logger.error("❌ Database connection failed: %s", error)
    db_pool = None


def get_db_connection():
    """Get a connection from the pool."""
    if db_pool:
        return db_pool.getconn()
    logger.warning("⚠️  No database pool available")
    return None


def release_db_connection(conn):
    """Return a connection back to the pool."""
    if db_pool and conn:
        db_pool.putconn(conn)


def execute_query(query, params=None, fetch_all=True):
    """Execute a SQL query and return results."""
    conn = get_db_connection()
    if not conn:
        logger.error("❌ Cannot execute query — no DB connection")
        return None

    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            if fetch_all:
                return cursor.fetchall()
            return cursor.fetchone()
    except Exception as e:
        logger.error("❌ Query error: %s", e)
        return None
    finally:
        release_db_connection(conn)
