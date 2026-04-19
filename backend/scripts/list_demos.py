#!/usr/bin/env python3
"""
Quick list of all demos from processed PPT documents.

Usage:
    cd backend
    python scripts/list_demos.py

    # Filter by document IDs
    python scripts/list_demos.py --document-ids 1,2,3

    # Show only demo types
    python scripts/list_demos.py --summary

    # Export as JSON
    python scripts/list_demos.py --json > demos.json
"""

import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from src.models.user import User
from src.models.ppt_document import PPTDocument
from src.core.database import SessionLocal


def list_all_demos(session: Session, document_ids: List[int] = None) -> List[Dict]:
    """List all demo HTMLs from processed documents."""
    query = session.query(PPTDocument).filter(PPTDocument.status == "ready")

    if document_ids:
        query = query.filter(PPTDocument.id.in_(document_ids))

    documents = query.all()
    all_demos = []

    for doc in documents:
        slides_data = doc.slides_data or {}
        slides = slides_data.get("slides", [])

        for slide in slides:
            if slide.get("needs_demo") and slide.get("demo_html"):
                all_demos.append({
                    "document_id": doc.id,
                    "document_title": doc.title,
                    "slide_number": slide.get("slide_number"),
                    "slide_title": slide.get("title", ""),
                    "demo_type": slide.get("demo_type", ""),
                    "demo_reason": slide.get("demo_reason", ""),
                    "html_length": len(slide["demo_html"]),
                    "subject": doc.subject or "",
                    "grade_level": doc.grade_level or 6
                })

    return all_demos


def print_demos_table(demos: List[Dict]):
    """Print demos in a formatted table."""
    if not demos:
        print("No demos found")
        return

    print("=" * 100)
    print(f"{'ID':<5} {'Document':<30} {'Slide':<20} {'Type':<15} {'Subject':<15} {'HTML Size':<10}")
    print("=" * 100)

    for demo in demos:
        doc_title = demo['document_title'][:27] + "..." if len(demo['document_title']) > 30 else demo['document_title']
        slide_title = demo['slide_title'][:17] + "..." if len(demo['slide_title']) > 20 else demo['slide_title']

        print(f"{demo['document_id']:<5} {doc_title:<30} {slide_title:<20} {demo['demo_type']:<15} "
              f"{demo['subject']:<15} {demo['html_length']:<10}")

    print("=" * 100)
    print(f"Total: {len(demos)} demo(s)")


def print_summary(demos: List[Dict]):
    """Print summary statistics."""
    if not demos:
        print("No demos found")
        return

    # Count by type
    type_counts = {}
    for demo in demos:
        demo_type = demo['demo_type'] or 'unknown'
        type_counts[demo_type] = type_counts.get(demo_type, 0) + 1

    # Count by subject
    subject_counts = {}
    for demo in demos:
        subject = demo['subject'] or 'unknown'
        subject_counts[subject] = subject_counts.get(subject, 0) + 1

    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    print(f"Total demos: {len(demos)}")

    print("\nBy Demo Type:")
    for demo_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {demo_type}: {count}")

    print("\nBy Subject:")
    for subject, count in sorted(subject_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {subject}: {count}")

    # Grade level distribution
    grade_counts = {}
    for demo in demos:
        grade = demo['grade_level']
        grade_counts[grade] = grade_counts.get(grade, 0) + 1

    print("\nBy Grade Level:")
    for grade, count in sorted(grade_counts.items()):
        print(f"  Grade {grade}: {count}")


def main():
    parser = argparse.ArgumentParser(
        description="List demos from processed PPT documents",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--document-ids',
        help='Comma-separated document IDs (e.g., 1,2,3)'
    )

    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show summary statistics only'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )

    args = parser.parse_args()

    # Parse document IDs
    document_ids = None
    if args.document_ids:
        document_ids = [int(id.strip()) for id in args.document_ids.split(',')]

    # Get session
    session = SessionLocal()

    try:
        # List demos
        demos = list_all_demos(session, document_ids)

        if args.json:
            print(json.dumps(demos, indent=2))
        elif args.summary:
            print_summary(demos)
        else:
            print_demos_table(demos)
            print_summary(demos)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
