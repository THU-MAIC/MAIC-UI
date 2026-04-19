"""
Demo Template API Endpoints

Provides endpoints for:
- Searching and browsing templates
- Template selection and preview
- Template-based content generation
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Optional, List
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..services.ai_processor import get_ai_processor

router = APIRouter()


class TemplateSearchRequest(BaseModel):
    """Request model for template search."""
    workflow_type: str = Field(..., description="Type of workflow: ppt_demo, website_pdf, website_concept")
    content_info: Dict = Field(..., description="Content information for matching")
    max_results: int = Field(5, ge=1, le=10, description="Maximum number of results to return")


class TemplateGenerateRequest(BaseModel):
    """Request model for template-based generation."""
    template_id: str = Field(..., description="ID of the selected template")
    workflow_type: str = Field(..., description="Type of workflow")
    content_info: Dict = Field(..., description="Content information")
    user_preferences: Dict = Field(default_factory=dict, description="User preferences")
    customization_params: Optional[Dict] = Field(None, description="Additional customization parameters")


@router.post("/search")
async def search_templates_for_selection(
    request: TemplateSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Search templates and return options for user to choose from.

    Request:
    {
        "workflow_type": "ppt_demo",
        "content_info": {
            "title": "Sorting Algorithms",
            "description": "Bubble sort visualization",
            "grade_level": 8,
            "demo_type": "simulation"
        },
        "max_results": 5
    }

    Response:
    {
        "status": "success",
        "templates_found": 3,
        "template_options": [
            {
                "template_id": "sorting_visualization",
                "display_name": "排序算法可视化",
                "match_score": 0.85,
                "match_reason": "匹配关键词: sorting | 类别匹配: algorithm | 适合8年级",
                "complexity": "medium",
                "usage_count": 150,
                "thumbnail": "/assets/sorting_thumb.png"
            }
        ]
    }
    """
    try:
        # Validate workflow type
        valid_workflow_types = ['ppt_demo', 'website_pdf', 'website_concept']
        if request.workflow_type not in valid_workflow_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid workflow_type. Must be one of: {', '.join(valid_workflow_types)}"
            )

        # Get AI processor
        ai_processor = get_ai_processor()

        # Search templates
        result = await ai_processor.search_templates_for_user(
            content_info=request.content_info,
            workflow_type=request.workflow_type,
            db_session_factory=get_db,
            max_results=request.max_results
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template search failed: {str(e)}")


@router.post("/generate")
async def generate_with_template(
    request: TemplateGenerateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate content using a user-selected template.

    Request:
    {
        "template_id": "sorting_visualization",
        "workflow_type": "ppt_demo",
        "content_info": {
            "title": "Sorting Algorithms",
            "description": "Bubble sort visualization"
        },
        "user_preferences": {
            "grade_level": 8,
            "interests": ["computer science"]
        },
        "customization_params": {
            "array_size": 10
        }
    }

    Response:
    {
        "status": "success",
        "html": "<!DOCTYPE html>...</html>",
        "metadata": {
            "template_used": "sorting_visualization",
            "generation_method": "template_based"
        }
    }
    """
    try:
        # Get AI processor
        ai_processor = get_ai_processor()

        # Generate with selected template
        result = await ai_processor.generate_with_selected_template(
            template_id=request.template_id,
            content_info=request.content_info,
            user_preferences=request.user_preferences,
            workflow_type=request.workflow_type,
            db_session_factory=get_db,
            customization_params=request.customization_params
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template generation failed: {str(e)}")


@router.get("/{template_id}/preview")
async def preview_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """
    Get template HTML with default/sample data for preview.

    Returns the original template HTML without customization.
    This endpoint is public (no authentication required) for template browsing.
    """
    try:
        from ..services.template_registry import get_template_registry

        registry = get_template_registry(lambda: db)
        template = registry.get_template_by_id(template_id)

        if not template:
            raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")

        return {
            "template_id": template_id,
            "display_name": template.display_name,
            "name": template.name,
            "workflow_type": template.workflow_type,
            "html": template.get_html_template()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template preview failed: {str(e)}")


@router.get("/browse")
async def browse_templates(
    workflow_type: Optional[str] = None,
    category: Optional[str] = None,
    grade_level: Optional[int] = None,
    subject_area: Optional[str] = None,
    complexity: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Browse templates with optional filters.

    Public endpoint (no authentication required) for template browsing.

    Query Parameters:
    - workflow_type: Filter by workflow type (ppt_demo, website_pdf, website_concept)
    - category: Filter by category
    - grade_level: Filter by grade level
    - subject_area: Filter by subject area
    - complexity: Filter by complexity (simple, medium, complex)
    - limit: Maximum results to return (default: 20)
    """
    try:
        from ..services.template_registry import get_template_registry

        registry = get_template_registry(lambda: db)

        templates = registry.browse_templates(
            workflow_type=workflow_type,
            category=category,
            grade_level=grade_level,
            subject_area=subject_area,
            complexity=complexity,
            limit=limit
        )

        return {
            "status": "success",
            "count": len(templates),
            "templates": templates
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template browse failed: {str(e)}")


@router.get("/categories")
async def get_template_categories(
    db: Session = Depends(get_db)
):
    """
    Get list of available template categories.

    Public endpoint (no authentication required).
    """
    try:
        from ..models.demo_template import DemoTemplate

        # Get all templates and extract unique categories
        templates = db.query(DemoTemplate).filter(
            DemoTemplate.is_active == True
        ).all()

        all_categories = set()
        for template in templates:
            if template.categories:
                all_categories.update(template.categories)

        return {
            "status": "success",
            "categories": sorted(list(all_categories))
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")


@router.get("/workflow-types")
async def get_workflow_types():
    """
    Get list of supported workflow types.

    Public endpoint (no authentication required).
    """
    return {
        "status": "success",
        "workflow_types": [
            {
                "type": "ppt_demo",
                "display_name": "PPT Demo",
                "description": "Interactive demos for PowerPoint presentations"
            },
            {
                "type": "website_pdf",
                "display_name": "Website from PDF",
                "description": "Convert PDFs to interactive learning websites"
            },
            {
                "type": "website_concept",
                "display_name": "Website from Concept",
                "description": "Generate learning websites from concept descriptions"
            }
        ]
    }
