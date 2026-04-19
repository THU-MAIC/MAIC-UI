# Template-Based Demo Library Design (Refined)

## Overview

The Template-Based Demo Library is a **database-backed, user-driven** system to accelerate interactive content generation across **all workflows** (PPT demos, website from PDF, website from concept). Instead of generating every demo from scratch using AI, the system allows users to select from pre-built, high-quality templates that are intelligently customized using LLMs.

## Key Changes from Original Plan

1. **Database-Backed Templates**: Templates stored in database (not Python files)
2. **User-Driven Selection**: Users choose templates instead of automatic matching
3. **LLM-Based Customization**: LLM (GLM-4.7) intelligently customizes templates (not simple placeholder replacement)
4. **All Workflows Supported**: PPT demos, website from PDF, and website from concept
5. **Configurable LLM**: Per-template or global LLM configuration

## Problem Statement

**Current Issues:**
- Every demo is generated from scratch using AI (slow: 10-30 seconds per demo)
- Inconsistent quality across generated demos
- High API costs for repetitive content (sorting algorithms, mathematical functions, etc.)
- No guarantee that generated code is bug-free or pedagogically sound
- Teachers wait 3-5 minutes for processing a 50-slide presentation

**Target Improvements:**
- 80% faster demo generation for common topics (templates: <2 seconds vs AI: 10-30 seconds)
- Consistent, tested, and verified interactive components
- 70-90% reduction in AI API costs for templated content
- Better pedagogical approach through proven template designs
- Professional-grade UI/UX across all demos
- **User control** over which template to use for their content

## Architecture Overview

### Workflow Comparison

**Before (Original Plan):**
```
Upload Content → Auto-Match Template → Customize with Placeholders → Return Result
```

**After (Refined Design):**
```
Upload Content → Search Templates → User Selects Template → LLM Customizes → Return Result
```

### Directory Structure

```
backend/
├── src/
│   ├── models/
│   │   └── demo_template.py              # Database model for templates
│   ├── services/
│   │   ├── template_registry.py          # Database-backed registry
│   │   ├── template_customizer.py        # LLM-based customization
│   │   ├── ai_processor.py               # Updated with template support
│   │   └── ppt_processor.py              # Updated with template workflow
│   ├── templates/                        # Template HTML files
│   │   ├── ppt_demo/
│   │   │   ├── sorting_visualization.html
│   │   │   ├── binary_search.html
│   │   │   └── ...
│   │   ├── website_pdf/
│   │   │   ├── science_lab.html
│   │   │   └── ...
│   │   └── website_concept/
│   │       ├── interactive_explanation.html
│   │       └── ...
│   └── api/
│       └── demo_templates.py             # Template API endpoints
└── migrations/
    └── create_demo_templates.py          # Database migration
```

---

## Section 1: Database Model

### DemoTemplate Model

```python
# backend/src/models/demo_template.py

from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.core.database import Base

class DemoTemplate(Base):
    """Database-backed demo template for PPT, website from PDF, and website from concept."""

    __tablename__ = "demo_templates"

    # Core identification
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    display_name = Column(String(200), nullable=False)

    # Template classification
    workflow_type = Column(String(50), nullable=False)  # 'ppt_demo', 'website_pdf', 'website_concept'
    categories = Column(JSON, default=list)  # ["algorithm", "mathematics", "science"]
    keywords = Column(JSON, default=list)
    keywords_zh = Column(JSON, default=list)

    # Educational metadata
    grade_levels = Column(JSON, default=list)  # [6, 7, 8, 9, 10, 11, 12]
    complexity = Column(String(20))  # "simple", "medium", "complex"
    subject_area = Column(String(100))  # "Computer Science", "Mathematics", etc.

    # Template file reference (HTML stored in files, not DB)
    html_template_path = Column(String(500), nullable=False)
    preview_thumbnail_path = Column(String(500))

    # LLM configuration for customization
    llm_config = Column(JSON, default=dict)  # {"provider": "zhipu", "model": "glm-4.7"}

    # Parameter schema for UI configuration
    parameter_schema = Column(JSON, default=dict)

    # Template content hints (helps LLM understand what to customize)
    customization_hints = Column(Text)

    # Template matching configuration
    matching_config = Column(JSON, default=dict)  # Weights for scoring factors

    # Version control
    version = Column(String(20), default="1.0.0")
    is_active = Column(Boolean, default=True)

    # Usage statistics
    usage_count = Column(Integer, default=0)
    average_rating = Column(Integer)  # 1-5 stars

    # Audit fields
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])

    def get_html_template(self) -> str:
        """Load HTML template from file."""
        from pathlib import Path
        template_path = Path(self.html_template_path)
        if template_path.exists():
            return template_path.read_text(encoding='utf-8')
        raise FileNotFoundError(f"Template HTML not found: {self.html_template_path}")

    def calculate_match_score(self, content_info: Dict) -> float:
        """Calculate template match score using configured weights."""
        weights = self.matching_config.get('weights', {
            'keywords': 0.4,
            'category': 0.3,
            'grade_level': 0.2,
            'subject': 0.1
        })

        score = 0.0

        # Keyword matching
        content_text = f"{content_info.get('title', '')} {content_info.get('description', '')}"
        all_keywords = (self.keywords or []) + (self.keywords_zh or [])
        keyword_matches = sum(1 for kw in all_keywords if kw.lower() in content_text.lower())
        score += (keyword_matches / max(len(all_keywords), 1)) * weights['keywords']

        # Category matching
        content_category = content_info.get('category', content_info.get('demo_type', ''))
        if content_category and content_category in self.categories:
            score += weights['category']

        # Grade level matching
        content_grade = content_info.get('grade_level', 6)
        if content_grade in self.grade_levels:
            score += weights['grade_level']

        # Subject area matching
        content_subject = content_info.get('subject', '')
        if content_subject and content_subject.lower() in self.subject_area.lower():
            score += weights['subject']

        return min(score, 1.0)
```

---

## Section 2: Template Customization Service

### LLM-Based Customization (Not Simple Replacement)

```python
# backend/src/services/template_customizer.py

class TemplateCustomizer:
    """
    Customize template HTML using LLM intelligence.

    Instead of simple placeholder replacement, the LLM:
    - Understands the template structure and preserves it
    - Intelligently adapts content based on user input
    - Maintains consistency with the template's design philosophy
    """

    async def customize_template(
        self,
        template: DemoTemplate,
        content_info: Dict,
        user_preferences: Dict,
        customization_params: Optional[Dict] = None
    ) -> str:
        """
        Customize template HTML using LLM.

        The LLM receives:
        1. Base template HTML
        2. Content information (title, description, concepts)
        3. User preferences (grade level, interests)
        4. Customization hints from template

        The LLM returns:
        - Customized HTML with preserved core structure
        - Modified content to match user's needs
        - Adjusted parameters and examples
        """

        # Load base template HTML
        base_html = template.get_html_template()

        # Determine which LLM to use (from template config)
        llm_config = template.llm_config or {"provider": "zhipu", "model": "glm-4.7"}

        # Build workflow-specific customization prompt
        prompt = self._build_customization_prompt(
            workflow_type=template.workflow_type,
            template=template,
            base_html=base_html,
            content_info=content_info,
            user_preferences=user_preferences
        )

        # Call LLM for customization
        customized_html = await self._call_llm_for_customization(prompt, llm_config)

        # Validate that structure is preserved
        if self._validate_customized_html(customized_html, base_html):
            return customized_html
        else:
            return self._generate_fallback_html(template, content_info)
```

**Key Prompt Strategy for Different Workflows:**

#### PPT Demo Customization Prompt:
```
你是交互式演示定制专家。请定制这个PPT演示模板。

【模板】排序算法可视化
【用途】simulation演示

【原始模板HTML】
[完整的HTML模板代码...]

【定制内容】
- 标题: Sorting Algorithms
- 描述: Bubble sort and merge sort visualization
- 演示原因: 需要逐步可视化排序过程

【学生】8年级，兴趣: computer science

【要求】
1. 保持模板的核心交互逻辑和视觉设计
2. 修改标题、描述等文本内容
3. 根据演示类型调整功能说明
4. 确保适合8年级理解
```

#### Website from PDF Customization Prompt:
```
你是交互式学习网站专家。请根据PDF分析定制这个网站模板。

【模板】科学实验室模板
【学科】Physics

【原始模板HTML】
[完整的HTML模板代码...]

【PDF分析】
- 学科: Physics
- 主题: Forces, Motion, Energy
- 概念: Newton's laws, friction, gravity

【学生】10年级

【要求】
1. 保持模板的导航和布局
2. 整合PDF的关键概念和主题
3. 根据内容调整实验和模拟
4. 保持所有交互功能可工作
```

#### Website from Concept Customization Prompt:
```
你是交互式教学专家。请根据知识点定制这个学习网站模板。

【模板】交互式解释模板
【知识点】Quadratic Equations

【原始模板HTML】
[完整的HTML模板代码...]

【知识点详情】
- 概述: 二次方程的图像和性质
- 掌握要点: 求解方法、图像特征、应用
- 设计思路: 交互式图像调整

【学生】9年级

【要求】
1. 根据设计思路实现交互组件
2. 为每个掌握要点创建学习模块
3. 提供清晰指导和即时反馈
4. 保持模板的视觉风格
```

---

## Section 3: Template Registry (Database-Backed)

### User-Driven Template Selection

```python
# backend/src/services/template_registry.py

class TemplateRegistry:
    """
    Central registry for demo templates backed by database.

    Key features:
    - Search templates by content matching
    - Return top K options for user selection
    - Explain match scores with human-readable reasons
    - Support browsing with filters
    """

    def search_templates_for_user_selection(
        self,
        content_info: Dict,
        workflow_type: str,
        max_results: int = 5
    ) -> List[Dict]:
        """
        Search and score templates for user to choose from.

        Returns:
        [
            {
                "template_id": "sorting_visualization",
                "display_name": "排序算法可视化",
                "match_score": 0.85,
                "match_reason": "匹配关键词: sorting, sort | 类别匹配: algorithm | 适合8年级",
                "complexity": "medium",
                "usage_count": 150,
                "thumbnail": "/assets/templates/sorting_thumb.png"
            },
            ...
        ]
        """

        # Query all active templates for workflow
        templates = db.query(DemoTemplate).filter(
            DemoTemplate.workflow_type == workflow_type,
            DemoTemplate.is_active == True
        ).all()

        # Score each template
        scored_templates = []
        for template in templates:
            score = template.calculate_match_score(content_info)

            if score >= 0.3:  # Minimum threshold
                match_reason = self._explain_match_score(template, content_info, score)

                scored_templates.append({
                    'template_id': template.template_id,
                    'display_name': template.display_name,
                    'match_score': round(score, 3),
                    'match_reason': match_reason,
                    'complexity': template.complexity,
                    'usage_count': template.usage_count,
                    'thumbnail': template.preview_thumbnail_path
                })

        # Sort by score and return top K
        scored_templates.sort(key=lambda x: x['match_score'], reverse=True)
        return scored_templates[:max_results]

    def _explain_match_score(self, template, content_info, score) -> str:
        """Generate human-readable match explanation."""
        reasons = []

        # Check keyword matches
        content_text = f"{content_info.get('title', '')} {content_info.get('description', '')}".lower()
        matched_keywords = [kw for kw in (template.keywords or [])
                          if kw.lower() in content_text]
        if matched_keywords:
            reasons.append(f"匹配关键词: {', '.join(matched_keywords[:3])}")

        # Check category match
        if content_info.get('demo_type') in template.categories:
            reasons.append(f"类别匹配: {content_info.get('demo_type')}")

        # Check grade level
        if content_info.get('grade_level') in template.grade_levels:
            reasons.append(f"适合{content_info.get('grade_level')}年级")

        return " | ".join(reasons)
```

---

## Section 4: AI Provider Integration

### Add Template Support to All Providers

```python
# backend/src/services/ai_processor.py

class AIProvider(ABC):
    """Abstract base class with template support."""

    @abstractmethod
    async def customize_template(
        self,
        template: DemoTemplate,
        content_info: Dict,
        user_preferences: Dict,
        customization_params: Optional[Dict] = None
    ) -> str:
        """Customize a template HTML using LLM."""
        pass


class ZhipuProvider(AIProvider):
    """Zhipu AI with template customization support."""

    async def customize_template(
        self,
        template: DemoTemplate,
        content_info: Dict,
        user_preferences: Dict,
        customization_params: Optional[Dict] = None
    ) -> str:
        """Customize template using GLM-4.7."""

        # Load base template
        base_html = template.get_html_template()

        # Build prompt based on workflow type
        if template.workflow_type == 'ppt_demo':
            prompt = self._build_ppt_prompt(template, base_html, content_info, user_preferences)
        elif template.workflow_type == 'website_pdf':
            prompt = self._build_website_pdf_prompt(template, base_html, content_info, user_preferences)
        elif template.workflow_type == 'website_concept':
            prompt = self._build_website_concept_prompt(template, base_html, content_info, user_preferences)

        # Call GLM-4.7 with thinking enabled for complex customization
        response = await self._run_zhipu_call(
            model=self.text_model,  # glm-4.7
            messages=[{"role": "user", "content": prompt}],
            thinking_params={"type": "enabled"}
        )

        # Extract and validate HTML
        customized_html = self._extract_html_from_response(response)
        return customized_html


class AIProcessor:
    """Main processor with user-driven template selection."""

    async def search_templates_for_user(
        self,
        content_info: Dict,
        workflow_type: str,
        db_session_factory,
        max_results: int = 5
    ) -> Dict:
        """
        Step 1: Search templates for user selection.

        Returns template options that user can review and choose from.
        """
        from .template_registry import get_template_registry

        registry = get_template_registry(db_session_factory)

        template_options = registry.search_templates_for_user_selection(
            content_info=content_info,
            workflow_type=workflow_type,
            max_results=max_results
        )

        return {
            "status": "success",
            "workflow_type": workflow_type,
            "templates_found": len(template_options),
            "template_options": template_options
        }

    async def generate_with_selected_template(
        self,
        template_id: str,
        content_info: Dict,
        user_preferences: Dict,
        workflow_type: str,
        db_session_factory,
        customization_params: Optional[Dict] = None
    ) -> Dict:
        """
        Step 2: Generate using user-selected template.
        """
        from .template_registry import get_template_registry

        registry = get_template_registry(db_session_factory)
        template = registry.get_template_by_id(template_id)

        if not template:
            return {"status": "error", "error": f"Template not found: {template_id}"}

        # Customize template using LLM
        customized_html = await self.provider.customize_template(
            template=template,
            content_info=content_info,
            user_preferences=user_preferences,
            customization_params=customization_params
        )

        return {
            "status": "success",
            "html": customized_html,
            "metadata": {
                "template_used": template_id,
                "template_name": template.display_name,
                "generation_method": "template_based"
            }
        }

    async def generate_without_template(
        self,
        content_info: Dict,
        user_preferences: Dict,
        workflow_type: str
    ) -> Dict:
        """
        Fallback: Generate without template (pure AI).
        """
        if workflow_type == 'website_pdf':
            return await self.provider.generate_website(
                images=content_info.get('images', []),
                analysis=content_info.get('analysis', {}),
                user_preferences=user_preferences
            )
        elif workflow_type == 'website_concept':
            return await self.provider.generate_website_from_concept(
                concept_data=content_info,
                user_preferences=user_preferences
            )
```

---

## Section 5: API Endpoints

### Template Selection & Generation API

```python
# backend/src/api/demo_templates.py

router = APIRouter()

@router.post("/templates/search")
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
                "thumbnail": "/assets/sorting_thumb.png"
            }
        ]
    }
    """
    ai_processor = get_ai_processor()
    return await ai_processor.search_templates_for_user(
        content_info=request.content_info,
        workflow_type=request.workflow_type,
        db_session_factory=get_db,
        max_results=request.max_results
    )


@router.post("/templates/generate")
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
        "content_info": {...},
        "user_preferences": {...},
        "customization_params": {"array_size": 10}
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
    ai_processor = get_ai_processor()
    return await ai_processor.generate_with_selected_template(
        template_id=request.template_id,
        content_info=request.content_info,
        user_preferences=request.user_preferences,
        workflow_type=request.workflow_type,
        db_session_factory=get_db,
        customization_params=request.customization_params
    )


@router.get("/templates/{template_id}/preview")
async def preview_template(template_id: str):
    """Get template HTML with default/sample data for preview."""
    registry = get_template_registry(get_db)
    template = registry.get_template_by_id(template_id)

    return {
        "template_id": template_id,
        "html": template.get_html_template(),
        "display_name": template.display_name
    }
```

---

## Section 6: Implementation Plan

### Phase 1: Database & Models (Week 1)

**Tasks:**
1. Create `DemoTemplate` model in `backend/src/models/demo_template.py`
2. Create database migration
3. Create template file storage structure
4. Seed initial templates

**Files:**
- `backend/src/models/demo_template.py`
- `backend/migrations/create_demo_templates.py`
- `backend/src/templates/` (directory structure)

### Phase 2: Core Services (Week 1-2)

**Tasks:**
1. Implement `TemplateCustomizer` service with LLM prompts
2. Implement `TemplateRegistry` service with search
3. Add `customize_template()` to `ZhipuProvider`
4. Update `AIProcessor` with template workflow methods

**Files:**
- `backend/src/services/template_customizer.py`
- `backend/src/services/template_registry.py`
- `backend/src/services/ai_processor.py` (modifications)

### Phase 3: API Endpoints (Week 2)

**Tasks:**
1. Create template API router
2. Register in main FastAPI app
3. Add authentication
4. Test endpoints

**Files:**
- `backend/src/api/demo_templates.py`
- `backend/src/main.py` (router registration)

### Phase 4: PPT Integration (Week 2-3)

**Tasks:**
1. Update `PPTDemoAnalyzer` for template workflow
2. Modify `process_ppt_background` to support template selection
3. Update processing results format

**Files:**
- `backend/src/services/ppt_processor.py`

**Workflow Change:**
```
Before: Upload → Analyze → Auto-Generate → Return
After:  Upload → Analyze → Search Templates → User Selects → Generate → Return
```

### Phase 5: Website Integration (Week 3-4)

**Tasks:**
1. Integrate templates into `generate_website` (PDF → Website)
2. Integrate templates into `generate_website_from_concept`
3. Add template browsing UI

**Files:**
- `backend/src/services/ai_processor.py` (website methods)

### Phase 6: Frontend Components (Week 4)

**Tasks:**
1. Create template selection UI
2. Create template browser
3. Create template preview component
4. Integrate with existing workflows

**Files:**
- `frontend/src/components/templates/TemplateSelector.tsx`
- `frontend/src/components/templates/TemplateBrowser.tsx`
- `frontend/src/components/templates/TemplatePreview.tsx`
- `frontend/src/services/api.ts` (template methods)

### Phase 7: Testing (Week 4-5)

**Testing Checklist:**
- Unit tests for template matching
- Integration tests for all workflows
- LLM customization quality tests
- Performance benchmarks

### Phase 8: Documentation & Deployment (Week 5)

**Documentation:**
- API documentation
- Template creation guide
- User guide for template selection

**Deployment:**
- Database migrations
- Template file deployment
- Environment configuration

---

## Section 7: Migration Strategy

### Step 1: Database Migration

```bash
# Create demo_templates table
cd backend
python -m migrations.create_demo_templates

# Seed initial templates
python -m migrations.seed_templates

# Verify
sqlite3 learn_your_way.db "SELECT COUNT(*) FROM demo_templates;"
```

### Step 2: Backward Compatibility

Keep existing methods with deprecation warnings:

```python
async def generate_demo_html(self, ...):
    """
    @deprecated Use template-based workflow instead.

    This method now internally uses template search + selection.
    """
    warnings.warn("Use template-based workflow", DeprecationWarning)

    # Try template-based first, fallback to AI-only
    template_search = await self._search_templates(...)
    if template_search['options']:
        return await self._generate_with_template(...)
    else:
        return await self._generate_with_ai_only(...)
```

### Step 3: Configuration

```python
# backend/config.py
TEMPLATE_CONFIG = {
    'template_dir': 'backend/src/templates',
    'cache_enabled': True,
    'cache_ttl': 300,
    'default_llm_provider': 'zhipu',
    'default_llm_model': 'glm-4.7',
    'max_template_results': 5,
    'min_template_score': 0.3
}
```

---

## Section 8: Success Metrics

### Template Coverage
- % of content finding ≥1 matching template (target: >80%)
- Number of active templates (target: 20+)
- Templates per category (target: 3-5 per major category)

### User Adoption
- % of generations using templates (target: >60%)
- Average template selection time (target: <30 seconds)
- Template diversity (avoid 1 template dominating)

### Performance
- Template search latency (target: <500ms)
- LLM customization time (target: <30s for GLM-4.7)
- Cost reduction vs pure AI (target: >50%)

### Quality
- User satisfaction ratings (target: >4.0/5.0)
- Template fallback rate to pure AI (target: <20%)
- Validation failure rate (target: <5%)

---

## Summary of Key Improvements

| Aspect | Original Plan | Refined Design |
|--------|--------------|----------------|
| **Template Storage** | Python files | Database + HTML files |
| **Template Selection** | Automatic matching | User-driven selection |
| **Customization** | Placeholder replacement | LLM-based customization |
| **Supported Workflows** | PPT demos only | PPT + Website PDF + Website Concept |
| **LLM Selection** | Fixed per provider | Configurable per template |
| **User Control** | None | Full template selection |
| **Match Explanation** | Scores only | Human-readable reasons |

---

## Next Steps

1. **Review this design** with team/stakeholders
2. **Create implementation tasks** from this plan
3. **Set up database** and seed initial templates
4. **Implement core services** (Customizer, Registry)
5. **Build API endpoints** for template workflow
6. **Integrate with existing** PPT and website generators
7. **Test with real content** and iterate on quality
8. **Deploy and monitor** success metrics
