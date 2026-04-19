#!/usr/bin/env python3
"""
Batch add websites as templates using command-line arguments.

This script supports both PDF documents and concept documents.

Usage examples:
    # Add all websites from documents 91, 92, 93 as templates
    python scripts/batch_add_website_templates.py --document-ids 91,92,93

    # Add with custom configuration
    python scripts/batch_add_website_templates.py --document-ids 91,92,93 --complexity medium --prefix mytemplate

    # List websites without adding
    python scripts/batch_add_website_templates.py --document-ids 91,92,93 --list-only
"""

import sys
import argparse
import re
from pathlib import Path
from typing import List, Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from src.models.user import User
from src.models.document import Document
from src.models.demo_template import DemoTemplate
from src.core.database import SessionLocal


def extract_websites(session: Session, document_ids: List[int]) -> List[Dict]:
    """Extract all website HTMLs from specified documents."""
    websites = []

    for doc_id in document_ids:
        doc = session.query(Document).filter(Document.id == doc_id).first()

        if not doc:
            print(f"⚠️  Document {doc_id} not found", file=sys.stderr)
            continue

        # Check if document has been processed
        if not doc.processing_results:
            print(f"⚠️  Document {doc_id} has no processing results", file=sys.stderr)
            continue

        # Get website HTML
        website_html = doc.processing_results.get("website", "")
        if not website_html:
            print(f"⚠️  Document {doc_id} has no website HTML", file=sys.stderr)
            continue

        # Determine workflow type
        has_concept_data = bool(doc.processing_results.get("concept_data"))
        workflow_type = "website_concept" if has_concept_data else "website_pdf"

        websites.append({
            "document_id": doc.id,
            "title": doc.title,
            "workflow_type": workflow_type,
            "html": website_html,
            "subject": doc.subject or "",
            "grade_level": doc.grade_level or 6,
            "concept_data": doc.processing_results.get("concept_data", {}),
            "description": doc.description or "",
            "analysis": doc.processing_results.get("analysis", {})
        })

    return websites


def create_template_config(website: Dict, options: Dict) -> Dict:
    """Create template config from website and CLI options."""
    # Generate template_id from title
    template_id = website['title'].lower()
    template_id = re.sub(r'[^\w\s-]', '', template_id)
    template_id = template_id.replace(' ', '_').replace('-', '_')[:50]
    template_id = '_'.join(template_id.split('_'))

    # Add prefix if specified
    if options.get('prefix'):
        template_id = f"{options['prefix']}_{template_id}"

    # Workflow type is auto-detected
    workflow_type = website['workflow_type']

    # Build categories
    categories = []
    if workflow_type == 'website_concept' and website['concept_data']:
        concept_name = website['concept_data'].get('concept_name', '')
        if concept_name:
            categories.append(concept_name)

    if website.get('analysis'):
        topics = website['analysis'].get('topics', [])
        if topics:
            categories.extend(topics[:2])

    if options.get('categories'):
        categories.extend(options['categories'].split(','))

    # Remove duplicates while preserving order
    categories = list(dict.fromkeys(categories))
    if not categories:
        categories = ['general']

    # Build HTML path
    templates_dir = Path(__file__).parent.parent / "src" / "templates" / workflow_type
    templates_dir.mkdir(parents=True, exist_ok=True)
    html_path = templates_dir / f"{template_id}.html"

    # Use relative path from backend directory
    relative_path = f"src/templates/{workflow_type}/{template_id}.html"

    # Build keywords from title and subject
    keywords = [website['subject'].lower(), 'interactive', 'learning']
    if options.get('keywords'):
        keywords.extend(options['keywords'].split(','))

    # Remove duplicates
    keywords = list(dict.fromkeys(keywords))

    # Build Chinese keywords
    keywords_zh = [website['title']] if website['title'] else []
    if options.get('keywords_zh'):
        keywords_zh.extend(options['keywords_zh'].split(','))

    keywords_zh = list(dict.fromkeys(keywords_zh))

    # Build customization hints
    hints = website['description']
    if workflow_type == 'website_concept' and website['concept_data']:
        cd = website['concept_data']
        hints = f"Concept: {cd.get('concept_name')}\n"
        hints += f"Overview: {cd.get('concept_overview')}\n"
        hints += f"Mastery: {cd.get('mastery_points')}\n"
        hints += f"Design: {cd.get('design_idea')}"

    if options.get('hints'):
        hints = options['hints']

    return {
        "template_id": template_id,
        "name": template_id,
        "display_name": options.get('display_name') or website['title'],
        "workflow_type": workflow_type,
        "categories": categories,
        "keywords": keywords[:10],
        "keywords_zh": keywords_zh[:10],
        "grade_levels": options.get('grade_levels', [website['grade_level']]),
        "complexity": options.get('complexity', 'medium'),
        "subject_area": options.get('subject_area') or website['subject'] or "General",
        "html_template_path": relative_path,
        "llm_config": {
            "provider": options.get('llm_provider', 'zhipu'),
            "model": options.get('llm_model', 'glm-4.7')
        },
        "customization_hints": hints or f"Auto-generated from {website['title']}",
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


def add_template(session: Session, website: Dict, config: Dict, dry_run: bool = False) -> bool:
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
    html_path.write_text(website['html'], encoding='utf-8')

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Batch add website demos as templates from PDF/concept documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all websites from documents 91,92,93
  python batch_add_website_templates.py --document-ids 91,92,93 --list-only

  # Add all websites as templates with default settings
  python batch_add_website_templates.py --document-ids 91,92,93

  # Add with custom settings
  python batch_add_website_templates.py --document-ids 91,92,93 --complexity medium --prefix mytemplate

  # Dry run (don't modify database)
  python batch_add_website_templates.py --document-ids 91,92,93 --dry-run
        """
    )

    parser.add_argument(
        '--document-ids',
        required=True,
        help='Comma-separated document IDs (e.g., 91,92,93)'
    )

    parser.add_argument(
        '--list-only',
        action='store_true',
        help='List websites without adding them'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate without modifying database'
    )

    parser.add_argument(
        '--complexity',
        choices=['simple', 'medium', 'complex'],
        default='medium',
        help='Template complexity (default: medium)'
    )

    parser.add_argument(
        '--categories',
        help='Comma-separated category tags (appended to auto-detected categories)'
    )

    parser.add_argument(
        '--subject-area',
        help='Subject area'
    )

    parser.add_argument(
        '--prefix',
        help='Prefix for template_id (e.g., "mytemplate" -> "mytemplate_trig_func")'
    )

    parser.add_argument(
        '--display-name',
        help='Display name template'
    )

    parser.add_argument(
        '--keywords',
        help='Comma-separated English keywords (appended to auto-generated keywords)'
    )

    parser.add_argument(
        '--keywords-zh',
        help='Comma-separated Chinese keywords (appended to auto-generated keywords)'
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
        # Extract websites
        websites = extract_websites(session, document_ids)

        if not websites:
            print(f"❌ No websites found in documents {document_ids}")
            return 1

        print(f"📊 Found {len(websites)} website(s) in {len(document_ids)} document(s)\n")

        # List only mode
        if args.list_only:
            print("="*70)
            print("Available Websites")
            print("="*70)
            for idx, website in enumerate(websites, 1):
                print(f"\n{idx}. Document: {website['title']} (ID: {website['document_id']})")
                print(f"   Type: {website['workflow_type']}")
                print(f"   Subject: {website['subject']} | Grade: {website['grade_level']}")
                if website['workflow_type'] == 'website_concept' and website['concept_data']:
                    cd = website['concept_data']
                    print(f"   Concept: {cd.get('concept_name', 'N/A')}")
                print(f"   HTML: {len(website['html'])} chars")
            return 0

        # Add templates mode
        print("="*70)
        print("Adding Templates")
        print("="*70)

        added_count = 0
        for website in websites:
            config = create_template_config(website, vars(args))
            if add_template(session, website, config, args.dry_run):
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

        # Count by workflow type
        pdf_count = session.query(DemoTemplate).filter(
            DemoTemplate.workflow_type == 'website_pdf',
            DemoTemplate.is_active == True
        ).count()
        concept_count = session.query(DemoTemplate).filter(
            DemoTemplate.workflow_type == 'website_concept',
            DemoTemplate.is_active == True
        ).count()
        ppt_count = session.query(DemoTemplate).filter(
            DemoTemplate.workflow_type == 'ppt_demo',
            DemoTemplate.is_active == True
        ).count()

        print(f"\n📊 Templates by type:")
        print(f"   PPT demos: {ppt_count}")
        print(f"   PDF websites: {pdf_count}")
        print(f"   Concept websites: {concept_count}")

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
