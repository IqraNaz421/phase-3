"""
Database migration runner for Phase 3: AI Chatbot
Runs SQL migration files using SQLAlchemy
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migration(migration_file: str):
    """Run a SQL migration file"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    # Read migration file
    with open(migration_file, 'r') as f:
        sql_content = f.read()

    # Create engine (synchronous for migration)
    # Convert asyncpg to psycopg2 for sync operations
    sync_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(sync_url)

    print(f"Running migration: {migration_file}")
    print(f"Database: {sync_url.split('@')[1]}")

    try:
        with engine.begin() as conn:
            # Execute migration SQL
            conn.execute(text(sql_content))

        print("[OK] Migration completed successfully")

        # Verify tables were created
        with engine.begin() as conn:
            result = conn.execute(text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('conversations', 'messages')
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]

            if 'conversations' in tables and 'messages' in tables:
                print("[OK] Verified: conversations and messages tables created")
            else:
                print(f"[WARNING] Expected tables not found. Found: {tables}")

        return True

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        return False

if __name__ == "__main__":
    migration_file = "migrations/003_add_conversations_messages.sql"
    success = run_migration(migration_file)
    sys.exit(0 if success else 1)
