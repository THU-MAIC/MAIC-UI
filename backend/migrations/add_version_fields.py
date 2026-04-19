"""
Migration script to add version management fields to documents table.

This script adds:
- root_document_id: Foreign key to the root document of the version chain
- version_number: Version number in the chain (1-based)
- is_current: Flag to indicate current version (1/0)
- user_prompt: Last user prompt used to edit the document

Run this script to update the database schema.
"""

import os
import sys

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from src.core.database import DATABASE_URL


def migrate():
    """Add version management fields to the documents table."""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if columns already exist (SQLite compatible)
        result = conn.execute(text("PRAGMA table_info(documents)"))
        existing_columns = [row[1] for row in result.fetchall()]
        
        migrations_needed = []
        
        if 'root_document_id' not in existing_columns:
            migrations_needed.append(
                "ALTER TABLE documents ADD COLUMN root_document_id INTEGER REFERENCES documents(id)"
            )
        
        if 'version_number' not in existing_columns:
            migrations_needed.append(
                "ALTER TABLE documents ADD COLUMN version_number INTEGER DEFAULT 1"
            )
        
        if 'is_current' not in existing_columns:
            migrations_needed.append(
                "ALTER TABLE documents ADD COLUMN is_current INTEGER DEFAULT 0"
            )

        if 'user_prompt' not in existing_columns:
            migrations_needed.append(
                "ALTER TABLE documents ADD COLUMN user_prompt VARCHAR"
            )
        
        if not migrations_needed:
            print("✅ All version fields already exist. No migration needed.")
            return
        
        print(f"📦 Running {len(migrations_needed)} migration(s)...")
        
        for sql in migrations_needed:
            print(f"   Executing: {sql}")
            conn.execute(text(sql))
        
        conn.commit()
        print("✅ Migration completed successfully!")
        
        # Create indexes for better query performance
        try:
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_documents_root_id ON documents(root_document_id)"
            ))
            conn.commit()
            print("✅ Indexes created successfully!")
        except Exception as e:
            print(f"⚠️ Index creation skipped (may already exist): {e}")


def rollback():
    """Remove version management fields from the documents table."""
    engine = create_engine(DATABASE_URL)
    
    print("⚠️ SQLite does not support DROP COLUMN directly.")
    print("   To rollback, you would need to:")
    print("   1. Create a new table without the version columns")
    print("   2. Copy data from the old table")
    print("   3. Drop the old table")
    print("   4. Rename the new table")
    print("   This operation is not implemented for safety reasons.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database migration for version management")
    parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
    args = parser.parse_args()
    
    if args.rollback:
        rollback()
    else:
        migrate()
