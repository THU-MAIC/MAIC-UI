"""
Migration script to remove version_label column from documents table.

SQLite does not support DROP COLUMN directly, so this migration
rebuilds the documents table without version_label.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from src.core.database import DATABASE_URL


def migrate():
	engine = create_engine(DATABASE_URL)

	with engine.connect() as conn:
		result = conn.execute(text("PRAGMA table_info(documents)"))
		existing_columns = [row[1] for row in result.fetchall()]

		if 'version_label' not in existing_columns:
			print("✅ No migration needed.")
			return

		print("📦 Rebuilding documents table to drop version_label...")
		conn.execute(text("PRAGMA foreign_keys=OFF"))
		conn.execute(text("ALTER TABLE documents RENAME TO documents_old"))

		conn.execute(text(
			"""
			CREATE TABLE documents (
				id INTEGER PRIMARY KEY,
				title VARCHAR NOT NULL,
				original_filename VARCHAR NOT NULL,
				file_path VARCHAR NOT NULL,
				file_size BIGINT,
				page_count INTEGER DEFAULT 0,
				subject VARCHAR,
				grade_level INTEGER DEFAULT 0,
				description VARCHAR,
				user_id INTEGER NOT NULL REFERENCES users(id),
				is_public BOOLEAN DEFAULT 0,
				status VARCHAR DEFAULT 'processing',
				pdf_metadata JSON,
				processing_results JSON,
				error_message VARCHAR,
				created_at DATETIME,
				updated_at DATETIME,
				root_document_id INTEGER REFERENCES documents(id),
				version_number INTEGER DEFAULT 1,
				is_current INTEGER DEFAULT 0,
				user_prompt VARCHAR
			)
			"""
		))

		conn.execute(text(
			"""
			INSERT INTO documents (
				id, title, original_filename, file_path, file_size, page_count, subject,
				grade_level, description, user_id, is_public, status, pdf_metadata,
				processing_results, error_message, created_at, updated_at,
				root_document_id, version_number, is_current, user_prompt
			)
			SELECT
				id, title, original_filename, file_path, file_size, page_count, subject,
				grade_level, description, user_id, is_public, status, pdf_metadata,
				processing_results, error_message, created_at, updated_at,
				root_document_id, version_number,
				0 AS is_current,
				user_prompt
			FROM documents_old
			"""
		))

		conn.execute(text("DROP TABLE documents_old"))
		conn.execute(text("CREATE INDEX IF NOT EXISTS idx_documents_root_id ON documents(root_document_id)"))
		conn.execute(text("PRAGMA foreign_keys=ON"))
		conn.commit()
		print("✅ Migration completed successfully!")


def rollback():
	print("⚠️ Rollback is not implemented for this migration.")


if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser(description="Remove version_label column")
	parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
	args = parser.parse_args()

	if args.rollback:
		rollback()
	else:
		migrate()
