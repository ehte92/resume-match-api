#!/usr/bin/env python3
"""
Create cover_letters table in the database.

This script manually creates the table since we don't have Alembic migrations set up yet.
Run this once to add the cover_letters table to your existing database.

Usage:
    python create_cover_letter_table.py
"""

from sqlalchemy import create_engine, text

from app.config import get_settings
from app.database import Base
from app.models.cover_letter import CoverLetter
from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis
from app.models.user import User

# Ensure all models are imported so SQLAlchemy knows about them


def create_cover_letter_table():
    """Create the cover_letters table in the database."""
    settings = get_settings()

    print("=" * 70)
    print("Creating cover_letters table")
    print("=" * 70)

    # Create engine
    engine = create_engine(settings.DATABASE_URL)

    # Create tables (only creates tables that don't exist)
    print(f"\nConnecting to database: {settings.DATABASE_URL.split('@')[1]}")
    Base.metadata.create_all(bind=engine, checkfirst=True)

    # Verify table was created
    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema='public'
            AND table_name='cover_letters'
        """
            )
        )
        if result.fetchone():
            print("✓ cover_letters table created successfully")
        else:
            print("✗ Failed to create cover_letters table")
            return False

        # Show table structure
        result = conn.execute(
            text(
                """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'cover_letters'
            ORDER BY ordinal_position
        """
            )
        )

        print("\nTable structure:")
        print(f"{'Column':<25} {'Type':<20} {'Nullable':<10}")
        print("-" * 55)
        for row in result:
            print(f"{row[0]:<25} {row[1]:<20} {row[2]:<10}")

    print("\n" + "=" * 70)
    print("Migration completed successfully!")
    print("=" * 70)
    return True


if __name__ == "__main__":
    try:
        success = create_cover_letter_table()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
