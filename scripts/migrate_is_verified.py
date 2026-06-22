import os
import sys

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app.core.database import engine


def migrate():
    try:
        with engine.connect() as conn:
            conn.execute(
                text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE")
            )
            conn.commit()
            print("Migration successful: Added is_verified column.")
    except Exception as e:
        print(f"Migration failed: {e}")


if __name__ == "__main__":
    migrate()
