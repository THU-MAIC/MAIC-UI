#!/usr/bin/env python3
"""
Add existing demo HTMLs from processed PPT documents as templates.

This script allows you to:
1. Enter PPT document IDs
2. Review their generated demo HTMLs
3. Customize template metadata
4. Add them to the demo_templates table

Usage:
    cd backend
    python scripts/add_demos_as_templates.py

Example interactive workflow:
    > Enter document IDs (comma-separated): 1, 2, 3
    > Found 3 documents with 7 demos total
    > [Review each demo and configure as template]
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from src.models.user import User
from src.models.ppt_document import PPTDocument
from src.models.demo_template import DemoTemplate
from src.core.database import SessionLocal


def list_document_demos(session: Session, document_ids: List[int]) -> List[Dict]:
    """
    Extract all demo HTMLs from specified documents.

    Returns:
        List of dicts with demo info:
        {
            "document_id": 1,
            "document_title": "Math Presentation",
            "slide_number": 2,
            "slide_title": "Sorting Algorithms",
            "demo_type": "simulation",
            "demo_reason": "Requires visualization",
            "demo_html": "<html>...</html>"
        }
    """
    demos = []

    for doc_id in document_ids:
        doc = session.query(PPTDocument).filter(PPTDocument.id == doc_id).first()

        if not doc:
            print(f"⚠️  Document {doc_id} not found")
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


def display_demo_preview(demo: Dict, index: int):
    """Display a preview of a demo for review."""
    print(f"\n{'='*70}")
    print(f"Demo #{index + 1}")
    print(f"{'='*70}")
    print(f"📄 Document: {demo['document_title']} (ID: {demo['document_id']})")
    print(f"📍 Slide {demo['slide_number']}: {demo['slide_title']}")
    print(f"🏷️  Demo Type: {demo['demo_type']}")
    print(f"📝 Reason: {demo['demo_reason']}")
    print(f"📚 Subject: {demo['subject']}")
    print(f"🎓 Grade Level: {demo['grade_level']}")
    print(f"\n📋 HTML Preview (first 500 chars):")
    print(f"   {demo['demo_html'][:500]}...")
    print(f"   (Total HTML length: {len(demo['demo_html'])} chars)")


def get_template_config_from_user(demo: Dict) -> Optional[Dict]:
    """
    Interactively collect template configuration from user.

    Returns:
        Template config dict or None if user skips
    """
    print(f"\n{'─'*70}")
    print("Configure as Template")
    print(f"{'─'*70}")

    # Auto-suggested template_id based on slide title
    suggestion = demo['slide_title'].lower().replace(' ', '_').replace('-', '_')[:50]
    suggestion = ''.join(c if c.isalnum() or c == '_' else '' for c in suggestion)

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
    existing = session.query(DemoTemplate).filter(DemoTemplate.template_id == template_id).first()
    if existing:
        print(f"   ⚠️  Template '{template_id}' already exists! Updating existing template.")

    # Display name
    display_name = input(f"2. display_name (shown to users) [{demo['slide_title']}]: ").strip()
    if not display_name:
        display_name = demo['slide_title']

    # Workflow type
    print("\n3. workflow_type:")
    print("   1 - ppt_demo (default)")
    print("   2 - website_pdf")
    print("   3 - website_concept")
    workflow_choice = input("   Choose [1]: ").strip() or "1"
    workflow_map = {"1": "ppt_demo", "2": "website_pdf", "3": "website_concept"}
    workflow_type = workflow_map.get(workflow_choice, "ppt_demo")

    # Categories
    print("\n4. categories (comma-separated tags, e.g., algorithm,math,science):")
    categories_input = input(f"   [{demo['demo_type']}]: ").strip()
    categories = [c.strip() for c in categories_input.split(',')] if categories_input else [demo['demo_type']]

    # Keywords (English)
    print("\n5. keywords (comma-separated English keywords):")
    keywords_input = input("   [e.g., sorting,algorithm,visualization]: ").strip()
    keywords = [k.strip() for k in keywords_input.split(',')] if keywords_input else []

    # Keywords (Chinese)
    print("\n6. keywords_zh (comma-separated Chinese keywords):")
    keywords_zh_input = input("   [e.g., 排序,算法,可视化]: ").strip()
    keywords_zh = [k.strip() for k in keywords_zh_input.split(',')] if keywords_zh_input else []

    # Grade levels
    print("\n7. grade_levels (comma-separated, e.g., 6,7,8,9,10,11,12):")
    grade_input = input(f"   [{demo['grade_level']}]: ").strip()
    if grade_input:
        grade_levels = [int(g.strip()) for g in grade_input.split(',')]
    else:
        grade_levels = [demo['grade_level']]

    # Complexity
    print("\n8. complexity:")
    print("   1 - simple")
    print("   2 - medium (default)")
    print("   3 - complex")
    complexity_choice = input("   Choose [2]: ").strip() or "2"
    complexity_map = {"1": "simple", "2": "medium", "3": "complex"}
    complexity = complexity_map.get(complexity_choice, "medium")

    # Subject area
    subject_area = input(f"\n9. subject_area [{demo['subject']}]: ").strip() or demo['subject'] or "General"

    # LLM Config
    print("\n10. LLM Config (press Enter for defaults):")
    print("    provider [zhipu]:")
    llm_provider = input("    ").strip() or "zhipu"
    print("    model [glm-4.7]:")
    llm_model = input("    ").strip() or "glm-4.7"

    # Customization hints
    print("\n11. customization_hints (instructions for LLM, press Enter to skip):")
    hints = input("    ").strip()

    # Save HTML file
    templates_dir = Path(__file__).parent.parent / "src" / "templates" / workflow_type
    templates_dir.mkdir(parents=True, exist_ok=True)

    html_filename = f"{template_id}.html"
    html_path = templates_dir / html_filename

    # Write HTML to file
    html_path.write_text(demo['demo_html'], encoding='utf-8')
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
        "customization_hints": hints if hints else f"Template based on {demo['document_title']}",
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
    print("Add Existing Demos as Templates")
    print("="*70)

    # Get document IDs from user
    while True:
        ids_input = input("\nEnter document IDs (comma-separated, e.g., 1,2,3): ").strip()
        if not ids_input:
            print("❌ Please enter at least one document ID")
            continue

        try:
            document_ids = [int(id.strip()) for id in ids_input.split(',')]
            break
        except ValueError:
            print("❌ Invalid format. Please enter comma-separated numbers (e.g., 1,2,3)")

    # Get session
    global session
    session = SessionLocal()

    try:
        # Extract all demos from documents
        demos = list_document_demos(session, document_ids)

        if not demos:
            print(f"\n⚠️  No demos found in documents {document_ids}")
            print("   Make sure documents have been processed and contain demo HTML")
            return

        print(f"\n✅ Found {len(demos)} demo(s) in {len(document_ids)} document(s)")

        # Review each demo
        for idx, demo in enumerate(demos):
            display_demo_preview(demo, idx)

            action = input(f"\n➤ Action? [a=add as template, s=skip, q=quit]: ").strip().lower()

            if action == 'q':
                print("\n👋 Quitting...")
                break
            elif action == 'a':
                config = get_template_config_from_user(demo)
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
