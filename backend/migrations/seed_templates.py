"""
Seed script to populate the demo_templates table with initial templates.

Run this script after creating the demo_templates table:
    python -m migrations.seed_templates
"""

import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.core.database import SessionLocal
from src.models.demo_template import DemoTemplate
from src.models import user  # Import user model to resolve relationships
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_initial_templates():
    """Get list of initial templates to seed."""
    return [
        {
            "template_id": "sorting_visualization",
            "name": "Sorting Algorithm Visualization",
            "display_name": "排序算法可视化",
            "workflow_type": "ppt_demo",
            "categories": ["algorithm", "computer_science", "sorting"],
            "keywords": ["sorting", "sort", "algorithm", "bubble", "merge", "quick"],
            "keywords_zh": ["排序", "算法", "冒泡排序", "归并排序", "快速排序"],
            "grade_levels": [6, 7, 8, 9, 10, 11, 12],
            "complexity": "medium",
            "subject_area": "Computer Science",
            "html_template_path": "src/templates/ppt_demo/sorting_visualization.html",
            "preview_thumbnail_path": None,
            "llm_config": {"provider": "zhipu", "model": "glm-4.7"},
            "customization_hints": "Template for visualizing sorting algorithms step by step",
            "matching_config": {
                "weights": {"keywords": 0.5, "category": 0.3, "grade_level": 0.15, "subject": 0.05}
            }
        },
        {
            "template_id": "binary_search_tree",
            "name": "Binary Search Tree Visualization",
            "display_name": "二叉搜索树可视化",
            "workflow_type": "ppt_demo",
            "categories": ["algorithm", "computer_science", "data_structure"],
            "keywords": ["binary", "search", "tree", "bst", "data structure"],
            "keywords_zh": ["二叉搜索树", "二叉树", "搜索", "数据结构"],
            "grade_levels": [8, 9, 10, 11, 12],
            "complexity": "complex",
            "subject_area": "Computer Science",
            "html_template_path": "src/templates/ppt_demo/binary_search_tree.html",
            "preview_thumbnail_path": None,
            "llm_config": {"provider": "zhipu", "model": "glm-4.7"},
            "customization_hints": "Template for binary search tree operations visualization",
            "matching_config": {
                "weights": {"keywords": 0.5, "category": 0.3, "grade_level": 0.15, "subject": 0.05}
            }
        },
        {
            "template_id": "science_lab_simulation",
            "name": "Science Lab Simulation",
            "display_name": "科学实验室模拟",
            "workflow_type": "website_pdf",
            "categories": ["science", "physics", "chemistry", "biology"],
            "keywords": ["experiment", "lab", "simulation", "science"],
            "keywords_zh": ["实验", "实验室", "模拟", "科学"],
            "grade_levels": [6, 7, 8, 9, 10],
            "complexity": "medium",
            "subject_area": "Science",
            "html_template_path": "src/templates/website_pdf/science_lab.html",
            "preview_thumbnail_path": None,
            "llm_config": {"provider": "zhipu", "model": "glm-4.7"},
            "customization_hints": "Template for science lab simulations with interactive experiments",
            "matching_config": {
                "weights": {"keywords": 0.4, "category": 0.3, "grade_level": 0.2, "subject": 0.1}
            }
        },
        {
            "template_id": "interactive_explanation",
            "name": "Interactive Explanation",
            "display_name": "交互式讲解",
            "workflow_type": "website_concept",
            "categories": ["general", "explanation", "tutorial"],
            "keywords": ["explanation", "tutorial", "learning", "guide"],
            "keywords_zh": ["讲解", "教程", "学习", "指南"],
            "grade_levels": [6, 7, 8, 9, 10, 11, 12],
            "complexity": "simple",
            "subject_area": "General Education",
            "html_template_path": "src/templates/website_concept/interactive_explanation.html",
            "preview_thumbnail_path": None,
            "llm_config": {"provider": "zhipu", "model": "glm-4.7"},
            "customization_hints": "General template for interactive concept explanations",
            "matching_config": {
                "weights": {"keywords": 0.3, "category": 0.3, "grade_level": 0.2, "subject": 0.2}
            }
        }
    ]


def seed_templates():
    """Seed the database with initial templates."""
    db = SessionLocal()
    try:
        logger.info("Starting template seeding...")

        # Check if templates already exist
        existing_count = db.query(DemoTemplate).count()
        if existing_count > 0:
            logger.info(f"ℹ️ Found {existing_count} existing templates, skipping seed")
            return

        # Create templates
        templates_data = get_initial_templates()
        created_count = 0

        for template_data in templates_data:
            try:
                template = DemoTemplate(**template_data)
                db.add(template)
                created_count += 1
                logger.info(f"✅ Added template: {template.display_name}")
            except Exception as e:
                logger.error(f"❌ Error adding template {template_data.get('display_name')}: {e}")

        db.commit()
        logger.info(f"🎉 Successfully seeded {created_count} templates")

    except Exception as e:
        logger.error(f"❌ Error seeding templates: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def verify_seeding():
    """Verify that templates were seeded successfully."""
    db = SessionLocal()
    try:
        count = db.query(DemoTemplate).count()
        logger.info(f"ℹ️ Total templates in database: {count}")
        return count > 0
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Starting template seeding...")

    seed_templates()

    if verify_seeding():
        logger.info("🎉 Template seeding completed successfully!")
        sys.exit(0)
    else:
        logger.error("⚠️ Template seeding may have failed")
        sys.exit(1)
