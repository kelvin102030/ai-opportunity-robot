import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).parent / "memory.db"


def connect():
    return sqlite3.connect(DB_PATH)


def initialize_memory():
    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                problem TEXT NOT NULL,
                solution TEXT,
                target_customer TEXT,
                revenue_potential TEXT,
                confidence REAL DEFAULT 0,
                status TEXT DEFAULT 'new',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id INTEGER NOT NULL,
                query TEXT,
                title TEXT,
                link TEXT,
                description TEXT,
                published TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (opportunity_id)
                    REFERENCES opportunities(id)
            )
        """)

        db.commit()


def remember_opportunity(
    title,
    problem,
    solution="",
    target_customer="",
    revenue_potential="",
    confidence=0,
    notes="",
):
    with connect() as db:
        existing = db.execute("""
            SELECT id
            FROM opportunities
            WHERE title = ?
              AND problem = ?
            ORDER BY id ASC
            LIMIT 1
        """, (title, problem)).fetchone()

        if existing:
            opportunity_id = existing[0]

            db.execute("""
                UPDATE opportunities
                SET solution = ?,
                    target_customer = ?,
                    revenue_potential = ?,
                    confidence = ?,
                    notes = ?
                WHERE id = ?
            """, (
                solution,
                target_customer,
                revenue_potential,
                confidence,
                notes,
                opportunity_id,
            ))

            db.commit()
            return opportunity_id

        cursor = db.execute("""
            INSERT INTO opportunities (
                title,
                problem,
                solution,
                target_customer,
                revenue_potential,
                confidence,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            problem,
            solution,
            target_customer,
            revenue_potential,
            confidence,
            notes,
        ))

        db.commit()
        return cursor.lastrowid


def remember_evidence(
    opportunity_id,
    query,
    title,
    link,
    description="",
    published="",
):
    with connect() as db:
        existing = db.execute("""
            SELECT id
            FROM evidence
            WHERE opportunity_id = ?
              AND link = ?
            LIMIT 1
        """, (opportunity_id, link)).fetchone()

        if existing:
            return existing[0]

        cursor = db.execute("""
            INSERT INTO evidence (
                opportunity_id,
                query,
                title,
                link,
                description,
                published
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            opportunity_id,
            query,
            title,
            link,
            description,
            published,
        ))

        db.commit()
        return cursor.lastrowid


def recall_opportunities():
    with connect() as db:
        return db.execute("""
            SELECT id,
                   title,
                   problem,
                   solution,
                   target_customer,
                   revenue_potential,
                   confidence,
                   status,
                   notes,
                   created_at
            FROM opportunities
            ORDER BY created_at DESC
        """).fetchall()


if __name__ == "__main__":
    initialize_memory()
    print("Robot memory initialized.")


def recall_evidence(opportunity_id):
    with connect() as db:
        return db.execute(
            """
            SELECT query, title, link, description, published
            FROM evidence
            WHERE opportunity_id = ?
            ORDER BY id ASC
            """,
            (opportunity_id,),
        ).fetchall()
