import sys
import os

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine

def migrate():
    print("Starting migration: Adding credits and is_beta_tester columns to users table...")
    with engine.connect() as connection:
        with connection.begin():
            try:
                connection.execute(text("ALTER TABLE users ADD COLUMN credits INTEGER DEFAULT 5"))
                print("- Added 'credits' column to 'users' table.")
            except Exception as e:
                print(f"- 'credits' column might already exist or error: {e}")

            try:
                connection.execute(text("ALTER TABLE users ADD COLUMN is_beta_tester BOOLEAN DEFAULT TRUE"))
                print("- Added 'is_beta_tester' column to 'users' table.")
            except Exception as e:
                print(f"- 'is_beta_tester' column might already exist or error: {e}")
                
            try:
                print("Creating 'purchase_intentions' table if it does not exist...")
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS purchase_intentions (
                        id VARCHAR PRIMARY KEY,
                        user_id VARCHAR NOT NULL REFERENCES users(id),
                        tier_requested VARCHAR NOT NULL,
                        clicked_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                print("- Created 'purchase_intentions' table.")
            except Exception as e:
                print(f"- Error creating 'purchase_intentions' table: {e}")

    print("Migration completed.")

if __name__ == "__main__":
    migrate()
