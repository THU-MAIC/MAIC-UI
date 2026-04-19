"""
Migration script to add template_options column to ppt_documents table.

Run this script to add the template_options field:
    python -m migrations.add_template_options_to_ppt
"""

import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.core.database import engine, SessionLocal, Base
from src.models.ppt_document import PPTDocument
from src.models import user
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_template_options_column():
    """Add the template_options column to ppt_documents table."""
    try:
        logger.info("Adding template_options column to ppt_documents table...")

        # Use SQLAlchemy to add the column
        from sqlalchemy import text

        with engine.begin() as conn:  # Use begin() for transaction management
            # Check if column already exists
            result = conn.execute(
                text("PRAGMA table_info(ppt_documents)")
            ).fetchall()

            column_names = [row[1] for row in result]

            if 'template_options' in column_names:
                logger.info("✅ Column template_options already exists")
                return

            # Add the column
            conn.execute(
                text("ALTER TABLE ppt_documents ADD COLUMN template_options JSON DEFAULT '{}'")
            )

        logger.info("✅ Successfully added template_options column")

    except Exception as e:
        logger.error(f"❌ Error adding template_options column: {e}")
        raise


def verify_migration():
    """Verify that the migration was successful."""
    try:
        from sqlalchemy import text

        with engine.connect() as conn:
            result = conn.execute(
                text("PRAGMA table_info(ppt_documents)")
            ).fetchall()

            column_names = [row[1] for row in result]

            if 'template_options' in column_names:
                logger.info("✅ Verification successful: template_options column exists")
                return True
            else:
                logger.error("❌ Verification failed: template_options column not found")
                return False

    except Exception as e:
        logger.error(f"❌ Error during verification: {e}")
        return False


if __name__ == "__main__":
    logger.info("Starting migration to add template_options column...")

    add_template_options_column()

    if verify_migration():
        logger.info("🎉 Migration completed successfully!")
        sys.exit(0)
    else:
        logger.error("⚠️ Migration completed with warnings")
        sys.exit(1)
