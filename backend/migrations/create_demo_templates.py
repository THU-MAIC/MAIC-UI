"""
Migration script to create the demo_templates table.

Run this script to initialize the demo_templates table in the database:
    python -m migrations.create_demo_templates
"""

import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.core.database import SessionLocal, engine, Base
from src.models.demo_template import DemoTemplate
from src.models import user  # Import user model to ensure users table exists
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_demo_templates_table():
    """Create the demo_templates table."""
    try:
        logger.info("Creating demo_templates table...")

        # Create the table
        DemoTemplate.__table__.create(engine, checkfirst=True)

        logger.info("✅ Successfully created demo_templates table")

    except Exception as e:
        logger.error(f"❌ Error creating demo_templates table: {e}")
        raise


def verify_table():
    """Verify that the table was created successfully."""
    try:
        from sqlalchemy import inspect

        inspector = inspect(engine)
        tables = inspector.get_table_names()

        if 'demo_templates' in tables:
            logger.info("✅ Verification successful: demo_templates table exists")
            return True
        else:
            logger.error("❌ Verification failed: demo_templates table not found")
            return False

    except Exception as e:
        logger.error(f"❌ Error during verification: {e}")
        return False


if __name__ == "__main__":
    logger.info("Starting demo_templates table migration...")

    create_demo_templates_table()

    if verify_table():
        logger.info("🎉 Migration completed successfully!")
        sys.exit(0)
    else:
        logger.error("⚠️ Migration completed with warnings")
        sys.exit(1)
