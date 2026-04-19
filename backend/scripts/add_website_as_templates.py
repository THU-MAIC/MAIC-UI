#!/usr/bin/env python3
"""
Add existing website HTMLs from processed PDF/concept documents as templates.

This script allows you to:
1. Enter document IDs (PDF or concept-based)
2. Review their generated website HTMLs
3. Customize template metadata
4. Add them to the demo_templates table

Usage:
    cd backend
    python scripts/add_website_as_templates.py

Example interactive workflow:
    > Enter document IDs (comma-separated): 91, 92, 93
    > Found 3 documents
    > [Review each website and configure as template]
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from src.models.user import User
from src.models.document import Document
from src.models.demo_template import DemoTemplate
from src.core.database import SessionLocal


def list_website_documents(session: Session, document_ids: List[int]) -> List[Dict]:
    """
    Extract all website HTMLs from specified documents.

    Returns:
        List of dicts with website info:
        {
            "document_id": 91,
            "title": "三角函数",
            "workflow_type": "website_pdf" or "website_concept",
            "html": "<html>...</html>",
            "subject": "数学",
            "grade_level": 12,
            "concept_data": {...}  # For concept-based documents
        }
    """
    websites = []

    for doc_id in document_ids:
        doc = session.query(Document).filter(Document.id == doc_id).first()

        if not doc:
            print(f"⚠️  Document {doc_id} not found")
            continue

        # Check if document has been processed
        if not doc.processing_results:
            print(f"⚠️  Document {doc_id} ({doc.title}) has no processing results")
            continue

        # Get website HTML
        website_html = doc.processing_results.get("website", "")
        if not website_html:
            print(f"⚠️  Document {doc_id} ({doc.title}) has no website HTML")
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


def display_website_preview(website: Dict, index: int):
    """Display a preview of a website for review."""
    print(f"\n{'='*70}")
    print(f"Website #{index + 1}")
    print(f"{'='*70}")
    print(f"📄 Document: {website['title']} (ID: {website['document_id']})")
    print(f"🔖 Type: {website['workflow_type']}")
    print(f"📚 Subject: {website['subject']}")
    print(f"🎓 Grade Level: {website['grade_level']}")

    if website['workflow_type'] == 'website_concept' and website['concept_data']:
        cd = website['concept_data']
        print(f"\n📖 Concept Information:")
        print(f"   Name: {cd.get('concept_name', 'N/A')}")
        print(f"   Overview: {cd.get('concept_overview', 'N/A')[:100]}...")
        print(f"   Mastery Points: {cd.get('mastery_points', 'N/A')[:100]}...")
        print(f"   Design Idea: {cd.get('design_idea', 'N/A')[:100]}...")

    if website['description']:
        print(f"\n📝 Description: {website['description'][:200]}...")

    print(f"\n📋 HTML Preview (first 500 chars):")
    print(f"   {website['html'][:500]}...")
    print(f"   (Total HTML length: {len(website['html'])} chars)")


def get_template_config_from_user(website: Dict) -> Optional[Dict]:
    """
    Interactively collect template configuration from user.

    Returns:
        Template config dict or None if user skips
    """
    print(f"\n{'─'*70}")
    print("Configure as Template")
    print(f"{'─'*70}")

    # Auto-suggested template_id based on title
    import re
    suggestion = website['title'].lower()
    suggestion = re.sub(r'[^\w\s-]', '', suggestion)  # Remove special chars
    suggestion = suggestion.replace(' ', '_').replace('-', '_')[:50]
    suggestion = '_'.join(suggestion.split('_'))  # Remove duplicate underscores

    print(f"\n📋 Template Configuration")
    print(f"{'─'*40}")

    # Get template_id (required, must be unique)
    while True:
        template_id = input(f"\n1. template_id (unique identifier) [{suggestion}]: ").strip()
        if not template_id:
            template_id = suggestion
        if template_id:
            break
        print("   ❌ template_id is required")

    # Check if template_id already exists
    session = SessionLocal()
    existing = session.query(DemoTemplate).filter(DemoTemplate.template_id == template_id).first()
    if existing:
        print(f"   ⚠️  Template '{template_id}' already exists! Updating existing template.")

    # Display name
    display_name = input(f"\n2. display_name (shown to users) [{website['title']}]: ").strip()
    if not display_name:
        display_name = website['title']

    # Workflow type (pre-determined)
    workflow_type = website['workflow_type']
    print(f"\n3. workflow_type: {workflow_type} (auto-detected)")

    # Categories
    default_categories = []
    if website['workflow_type'] == 'website_concept' and website['concept_data']:
        # Use concept name as category
        concept_name = website['concept_data'].get('concept_name', '')
        if concept_name:
            default_categories.append(concept_name)
    elif website.get('analysis'):
        # Use topics from analysis
        topics = website['analysis'].get('topics', [])
        if topics:
            default_categories.extend(topics[:2])

    default_cats_str = ','.join(default_categories) if default_categories else ''
    print(f"\n4. categories (comma-separated tags)")
    categories_input = input(f"   [{default_cats_str}]: ").strip()
    if categories_input:
        categories = [c.strip() for c in categories_input.split(',')]
    else:
        categories = default_categories if default_categories else ['general']

    # Keywords (English)
    print(f"\n5. keywords (comma-separated English keywords)")
    keywords_input = input(f"   [e.g., interactive,learning,{website['subject'].lower()}]: ").strip()
    if keywords_input:
        keywords = [k.strip() for k in keywords_input.split(',')]
    else:
        keywords = [website['subject'].lower(), 'interactive', 'learning']

    # Keywords (Chinese)
    print(f"\n6. keywords_zh (comma-separated Chinese keywords)")
    keywords_zh_input = input(f"   [e.g., {website['title']}]: ").strip()
    if keywords_zh_input:
        keywords_zh = [k.strip() for k in keywords_zh_input.split(',')]
    else:
        keywords_zh = [website['title']] if website['title'] else []

    # Grade levels
    print(f"\n7. grade_levels (comma-separated, e.g., 6,7,8,9,10,11,12)")
    grade_input = input(f"   [{website['grade_level']}]: ").strip()
    if grade_input:
        grade_levels = [int(g.strip()) for g in grade_input.split(',')]
    else:
        grade_levels = [website['grade_level']]

    # Complexity
    print(f"\n8. complexity:")
    print("   1 - simple")
    print("   2 - medium (default)")
    print("   3 - complex")
    complexity_choice = input("   Choose [2]: ").strip() or "2"
    complexity_map = {"1": "simple", "2": "medium", "3": "complex"}
    complexity = complexity_map.get(complexity_choice, "medium")

    # Subject area
    subject_area = input(f"\n9. subject_area [{website['subject']}]: ").strip() or website['subject'] or "General"

    # LLM Config
    print(f"\n10. LLM Config (press Enter for defaults):")
    print("    provider [zhipu]:")
    llm_provider = input("    ").strip() or "zhipu"
    print("    model [glm-4.7]:")
    llm_model = input("    ").strip() or "glm-4.7"

    # Customization hints
    hints = website['description']
    if website['workflow_type'] == 'website_concept' and website['concept_data']:
        cd = website['concept_data']
        hints = f"Concept: {cd.get('concept_name')}\n"
        hints += f"Overview: {cd.get('concept_overview')}\n"
        hints += f"Mastery: {cd.get('mastery_points')}\n"
        hints += f"Design: {cd.get('design_idea')}"

    print(f"\n11. customization_hints (instructions for LLM, press Enter to use default)")
    print(f"    Default: {hints[:100]}...")
    user_hints = input("    ").strip()
    if user_hints:
        hints = user_hints

    # Save HTML file
    templates_dir = Path(__file__).parent.parent / "src" / "templates" / workflow_type
    templates_dir.mkdir(parents=True, exist_ok=True)

    html_filename = f"{template_id}.html"
    html_path = templates_dir / html_filename

    # Write HTML to file
    html_path.write_text(website['html'], encoding='utf-8')
    print(f"\n✅ HTML saved to: {html_path}")

    # Use relative path from backend directory
    relative_path = f"src/templates/{workflow_type}/{html_filename}"

    return {
        "template_id": template_id,
        "name": template_id,
        "display_name": display_name,
        "workflow_type": workflow_type,
        "categories": categories,
        "keywords": keywords,
        "keywords_zh": keywords_zh,
        "grade_levels": grade_levels,
        "complexity": complexity,
        "subject_area": subject_area,
        "html_template_path": relative_path,
        "llm_config": {
            "provider": llm_provider,
            "model": llm_model
        },
        "customization_hints": hints,
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


def create_or_update_template(session: Session, config: Dict) -> DemoTemplate:
    """Create a new template or update existing one."""
    existing = session.query(DemoTemplate).filter(
        DemoTemplate.template_id == config["template_id"]
    ).first()

    if existing:
        # Update existing template
        for key, value in config.items():
            setattr(existing, key, value)
        print(f"✅ Updated template: {config['template_id']}")
        return existing
    else:
        # Create new template
        template = DemoTemplate(**config)
        session.add(template)
        print(f"✅ Created template: {config['template_id']}")
        return template


def main():
    """Main interactive script."""
    print("="*70)
    print("Add Existing Websites as Templates")
    print("="*70)
    print("\nSupported document types:")
    print("  • PDF documents (website_pdf)")
    print("  • Concept-based documents (website_concept)")

    # Get document IDs from user
    while True:
        ids_input = input("\nEnter document IDs (comma-separated, e.g., 91,92,93): ").strip()
        if not ids_input:
            print("❌ Please enter at least one document ID")
            continue

        try:
            document_ids = [int(id.strip()) for id in ids_input.split(',')]
            break
        except ValueError:
            print("❌ Invalid format. Please enter comma-separated numbers (e.g., 91,92,93)")

    # Get session
    global session
    session = SessionLocal()

    try:
        # Extract all websites from documents
        websites = list_website_documents(session, document_ids)

        if not websites:
            print(f"\n⚠️  No websites found in documents {document_ids}")
            print("   Make sure documents have been processed and contain website HTML")
            return

        print(f"\n✅ Found {len(websites)} website(s) in {len(document_ids)} document(s)")

        # Review each website
        for idx, website in enumerate(websites):
            display_website_preview(website, idx)

            action = input(f"\n➤ Action? [a=add as template, s=skip, q=quit]: ").strip().lower()

            if action == 'q':
                print("\n👋 Quitting...")
                break
            elif action == 'a':
                config = get_template_config_from_user(website)
                if config:
                    create_or_update_template(session, config)
                    session.commit()
            elif action == 's':
                print("⏭️  Skipped")
                continue

        # Summary
        print("\n" + "="*70)
        print("Summary")
        print("="*70)

        template_count = session.query(DemoTemplate).count()
        print(f"📊 Total templates in database: {template_count}")

        active_count = session.query(DemoTemplate).filter(DemoTemplate.is_active == True).count()
        print(f"✅ Active templates: {active_count}")

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

        print("\n✅ Done! Templates have been added to the database.")
        print("\n💡 Next steps:")
        print("   1. Review templates in the database")
        print("   2. Test template generation using the API")
        print("   3. Browse templates at /api/templates/browse")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    main()
