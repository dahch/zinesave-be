import os
import sys

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app.core.database import engine


def migrate():
    print("Starting migration: Adding is_deleted and deleted_at columns to files table...")
    with engine.connect() as connection:
        with connection.begin():
            # Check if columns exist to avoid errors if run multiple times
            # This is a basic check for PostgreSQL/SQLite compatibility
            try:
                connection.execute(
                    text("ALTER TABLE files ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE")
                )
                print("- Added 'is_deleted' column.")
            except Exception as e:
                print(f"- 'is_deleted' column might already exist or error: {e}")

            try:
                connection.execute(text("ALTER TABLE files ADD COLUMN deleted_at TIMESTAMPTZ NULL"))
                print("- Added 'deleted_at' column.")
            except Exception as e:
                print(f"- 'deleted_at' column might already exist or error: {e}")

    print("Migration completed.")


if __name__ == "__main__":
    migrate()
