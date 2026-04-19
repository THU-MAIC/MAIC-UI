#!/usr/bin/env python3
"""
Batch add demos as templates using command-line arguments.

Usage examples:
    # Add all demos from documents 1, 2, 3 as templates
    python scripts/batch_add_templates.py --document-ids 1,2,3

    # Add with custom configuration
    python scripts/batch_add_templates.py --document-ids 1,2,3 --workflow-type ppt_demo --complexity medium

    # List demos without adding
    python scripts/batch_add_templates.py --document-ids 1,2,3 --list-only
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from src.models.user import User
from src.models.ppt_document import PPTDocument
from src.models.demo_template import DemoTemplate
from src.core.database import SessionLocal


def extract_demos(session: Session, document_ids: List[int]) -> List[Dict]:
    """Extract all demo HTMLs from specified documents."""
    demos = []

    for doc_id in document_ids:
        doc = session.query(PPTDocument).filter(PPTDocument.id == doc_id).first()

        if not doc:
            print(f"⚠️  Document {doc_id} not found", file=sys.stderr)
            continue

        slides_data = doc.slides_data or {}
        slides = slides_data.get("slides", [])

        for slide in slides:
            if slide.get("needs_demo") and slide.get("demo_html"):
                demos.append({
                    "document_id": doc.id,
                    "document_title": doc.title,
                    "slide_number": slide.get("slide_number"),
                    "slide_title": slide.get("title", ""),
                    "demo_type": slide.get("demo_type", ""),
                    "demo_reason": slide.get("demo_reason", ""),
                    "demo_html": slide["demo_html"],
                    "subject": doc.subject or "",
                    "grade_level": doc.grade_level or 6
                })

    return demos


def create_template_config(demo: Dict, options: Dict) -> Dict:
    """Create template config from demo and CLI options."""
    # Generate template_id from slide title
    template_id = demo['slide_title'].lower().replace(' ', '_').replace('-', '_')[:50]
    template_id = ''.join(c if c.isalnum() or c == '_' else '' for c in template_id)

    # Add prefix if specified
    if options.get('prefix'):
        template_id = f"{options['prefix']}_{template_id}"

    # Determine workflow type
    workflow_type = options.get('workflow_type', 'ppt_demo')

    # Build categories
    categories = [demo['demo_type']] if demo['demo_type'] else []
    if options.get('categories'):
        categories.extend(options['categories'].split(','))

    # Build HTML path
    templates_dir = Path(__file__).parent.parent / "src" / "templates" / workflow_type
    templates_dir.mkdir(parents=True, exist_ok=True)
    html_path = templates_dir / f"{template_id}.html"

    # Use relative path from backend directory
    relative_path = f"src/templates/{workflow_type}/{template_id}.html"

    # Build keywords from title and type
    keywords = []
    if demo['slide_title']:
        # Extract simple keywords from title
        words = demo['slide_title'].lower().replace('-', ' ').split()
        keywords.extend([w for w in words if len(w) > 3])
    if demo['demo_type']:
        keywords.append(demo['demo_type'].lower())

    return {
        "template_id": template_id,
        "name": template_id,
        "display_name": options.get('display_name') or demo['slide_title'],
        "workflow_type": workflow_type,
        "categories": categories,
        "keywords": keywords[:10],  # Limit to 10 keywords
        "keywords_zh": options.get('keywords_zh', []).split(',') if options.get('keywords_zh') else [],
        "grade_levels": options.get('grade_levels', [demo['grade_level']]),
        "complexity": options.get('complexity', 'medium'),
        "subject_area": options.get('subject_area') or demo['subject'] or "General",
        "html_template_path": relative_path,
        "llm_config": {
            "provider": options.get('llm_provider', 'zhipu'),
            "model": options.get('llm_model', 'glm-4.7')
        },
        "customization_hints": options.get('hints') or f"Auto-generated from {demo['document_title']}",
        "matching_config": {
            "weights": {
                "keywords": 0.4,
                "category": 0.3,
                "grade_level": 0.2,
                "subject": 0.1
            }
        },
        "is_active": True,
        "version": "1.0.0"
    }


def add_template(session: Session, demo: Dict, config: Dict, dry_run: bool = False) -> bool:
    """Add a template to the database."""
    if not dry_run:
        # Check if exists
        existing = session.query(DemoTemplate).filter(
            DemoTemplate.template_id == config["template_id"]
        ).first()

        if existing:
            if config.get('overwrite'):
                # Update
                for key, value in config.items():
                    setattr(existing, key, value)
                print(f"✅ Updated: {config['template_id']}")
                return True
            else:
                print(f"⏭️  Skipped (exists): {config['template_id']}")
                return False
        else:
            # Create new
            template = DemoTemplate(**config)
            session.add(template)
            print(f"✅ Created: {config['template_id']}")

    # Write HTML file
    html_path = Path(config['html_template_path'])
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(demo['demo_html'], encoding='utf-8')

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Batch add PPT demos as templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all demos from documents 1,2,3
  python batch_add_templates.py --document-ids 1,2,3 --list-only

  # Add all demos as templates with default settings
  python batch_add_templates.py --document-ids 1,2,3

  # Add with custom settings
  python batch_add_templates.py --document-ids 1,2,3 --workflow-type ppt_demo --complexity medium --prefix mytemplate

  # Dry run (don't modify database)
  python batch_add_templates.py --document-ids 1,2,3 --dry-run
        """
    )

    parser.add_argument(
        '--document-ids',
        required=True,
        help='Comma-separated document IDs (e.g., 1,2,3)'
    )

    parser.add_argument(
        '--list-only',
        action='store_true',
        help='List demos without adding them'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate without modifying database'
    )

    parser.add_argument(
        '--workflow-type',
        choices=['ppt_demo', 'website_pdf', 'website_concept'],
        default='ppt_demo',
        help='Template workflow type (default: ppt_demo)'
    )

    parser.add_argument(
        '--complexity',
        choices=['simple', 'medium', 'complex'],
        default='medium',
        help='Template complexity (default: medium)'
    )

    parser.add_argument(
        '--categories',
        help='Comma-separated category tags'
    )

    parser.add_argument(
        '--subject-area',
        help='Subject area'
    )

    parser.add_argument(
        '--prefix',
        help='Prefix for template_id (e.g., "mytemplate" -> "mytemplate_sorting_algo")'
    )

    parser.add_argument(
        '--display-name',
        help='Display name template (use "{title}" for slide title)'
    )

    parser.add_argument(
        '--keywords-zh',
        help='Comma-separated Chinese keywords'
    )

    parser.add_argument(
        '--grade-levels',
        type=lambda x: [int(i) for i in x.split(',')],
        help='Comma-separated grade levels (e.g., 6,7,8,9,10,11,12)'
    )

    parser.add_argument(
        '--llm-provider',
        default='zhipu',
        help='LLM provider (default: zhipu)'
    )

    parser.add_argument(
        '--llm-model',
        default='glm-4.7',
        help='LLM model (default: glm-4.7)'
    )

    parser.add_argument(
        '--hints',
        help='Customization hints for LLM'
    )

    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing templates'
    )

    args = parser.parse_args()

    # Parse document IDs
    document_ids = [int(id.strip()) for id in args.document_ids.split(',')]

    # Get session
    session = SessionLocal()

    try:
        # Extract demos
        demos = extract_demos(session, document_ids)

        if not demos:
            print(f"❌ No demos found in documents {document_ids}")
            return 1

        print(f"📊 Found {len(demos)} demo(s) in {len(document_ids)} document(s)\n")

        # List only mode
        if args.list_only:
            print("="*70)
            print("Available Demos")
            print("="*70)
            for idx, demo in enumerate(demos, 1):
                print(f"\n{idx}. Document: {demo['document_title']} (ID: {demo['document_id']})")
                print(f"   Slide {demo['slide_number']}: {demo['slide_title']}")
                print(f"   Type: {demo['demo_type']} | Subject: {demo['subject']} | Grade: {demo['grade_level']}")
                print(f"   HTML: {len(demo['demo_html'])} chars")
            return 0

        # Add templates mode
        print("="*70)
        print("Adding Templates")
        print("="*70)

        added_count = 0
        for demo in demos:
            config = create_template_config(demo, vars(args))
            if add_template(session, demo, config, args.dry_run):
                added_count += 1

        if not args.dry_run:
            session.commit()
            print(f"\n✅ Added {added_count} template(s)")
        else:
            print(f"\n🔍 Dry run: Would add {added_count} template(s)")

        # Summary
        total_templates = session.query(DemoTemplate).count()
        active_templates = session.query(DemoTemplate).filter(DemoTemplate.is_active == True).count()
        print(f"\n📊 Database stats:")
        print(f"   Total templates: {total_templates}")
        print(f"   Active templates: {active_templates}")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        session.rollback()
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
