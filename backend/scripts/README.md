# Template Management Scripts

This directory contains scripts to easily convert existing demo/website HTMLs from processed documents into reusable templates.

## Quick Reference

| If you want to... | Use this script |
|-------------------|-----------------|
| Add PPT demos interactively | `add_demos_as_templates.py` |
| Batch add PPT demos | `batch_add_templates.py` |
| Add PDF/Concept websites interactively | `add_website_as_templates.py` |
| Batch add PDF/Concept websites | `batch_add_website_templates.py` |

## Overview

When you process documents (PPT files, PDFs, or concept inputs), the system generates interactive HTML content. These scripts help you:

1. Extract HTMLs from processed documents (PPT, PDF, or concept-based)
2. Save them as template files
3. Add them to the `demo_templates` database table
4. Configure template metadata (keywords, categories, grade levels, etc.)

### Supported Document Types

| Document Type | Workflow Type | Source |
|--------------|--------------|--------|
| PPT Documents | `ppt_demo` | `ppt_documents` table |
| PDF Documents | `website_pdf` | `documents` table (PDF uploads) |
| Concept Documents | `website_concept` | `documents` table (concept inputs) |

---

## Script 1: Interactive Template Creator

**File:** `add_demos_as_templates.py`

Interactively review demos and configure them as templates one by one.

### Usage

```bash
cd backend
python scripts/add_demos_as_templates.py
```

### Interactive Workflow

1. Enter comma-separated document IDs (e.g., `1,2,3`)
2. The script displays each demo with:
   - Document title and ID
   - Slide number and title
   - Demo type and reason
   - HTML preview
3. For each demo, choose:
   - `a` - Add as template (configure metadata)
   - `s` - Skip this demo
   - `q` - Quit
4. If adding, configure:
   - `template_id` - Unique identifier
   - `display_name` - Name shown to users
   - `workflow_type` - ppt_demo, website_pdf, website_concept
   - `categories` - Category tags
   - `keywords` - English keywords
   - `keywords_zh` - Chinese keywords
   - `grade_levels` - Applicable grades
   - `complexity` - simple, medium, complex
   - `subject_area` - Subject area
   - LLM configuration (provider, model)
   - Customization hints

### Example Session

```
Enter document IDs (comma-separated): 1,2,3

======================================================================
Demo #1
======================================================================
📄 Document: Sorting Algorithms (ID: 1)
📍 Slide 2: Bubble Sort Visualization
🏷️  Demo Type: simulation
📝 Reason: Requires step-by-step visualization
📚 Subject: Computer Science
🎓 Grade Level: 8

➤ Action? [a=add as template, s=skip, q=quit]: a

Configure as Template
──────────────────────────────────────────────────────────────────

1. template_id (unique identifier) [bubble_sort_visualization]:
2. display_name (shown to users) [Bubble Sort Visualization]:
3. workflow_type:
   1 - ppt_demo (default)
   2 - website_pdf
   3 - website_concept
   Choose [1]:
...
✅ Created template: bubble_sort_visualization
✅ HTML saved to: backend/src/templates/ppt_demo/bubble_sort_visualization.html
```

---

## Script 2: Batch Template Creator

**File:** `batch_add_templates.py`

Batch process multiple demos with command-line arguments. Ideal for automation.

### Basic Usage

```bash
# List all demos from documents
python scripts/batch_add_templates.py --document-ids 1,2,3 --list-only

# Add all demos with default settings
python scripts/batch_add_templates.py --document-ids 1,2,3

# Dry run (preview without modifying database)
python scripts/batch_add_templates.py --document-ids 1,2,3 --dry-run
```

### Advanced Options

```bash
python scripts/batch_add_templates.py \
    --document-ids 1,2,3 \
    --workflow-type ppt_demo \
    --complexity medium \
    --categories algorithm,sorting \
    --subject-area "Computer Science" \
    --grade-levels 6,7,8,9,10,11,12 \
    --prefix mytemplate \
    --overwrite
```

### All Options

| Option | Description | Default |
|--------|-------------|---------|
| `--document-ids` | Comma-separated document IDs (required) | - |
| `--list-only` | List demos without adding them | False |
| `--dry-run` | Simulate without modifying database | False |
| `--workflow-type` | ppt_demo, website_pdf, website_concept | ppt_demo |
| `--complexity` | simple, medium, complex | medium |
| `--categories` | Comma-separated category tags | From demo |
| `--subject-area` | Subject area | From document |
| `--prefix` | Prefix for template_id | None |
| `--display-name` | Display name template | From slide |
| `--keywords-zh` | Comma-separated Chinese keywords | Empty |
| `--grade-levels` | Comma-separated grade levels | From document |
| `--llm-provider` | LLM provider | zhipu |
| `--llm-model` | LLM model | glm-4.7 |
| `--hints` | Customization hints | Auto-generated |
| `--overwrite` | Overwrite existing templates | False |

---

## Template Files Location

Templates are saved to:

```
backend/src/templates/
├── ppt_demo/
│   ├── sorting_visualization.html
│   ├── bubble_sort.html
│   └── ...
├── website_pdf/
│   └── science_lab.html
└── website_concept/
    └── interactive_explanation.html
```

---

## Database Schema

Templates are stored in the `demo_templates` table:

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| template_id | String(100) | Unique template identifier |
| display_name | String(200) | Display name (shown to users) |
| workflow_type | String(50) | ppt_demo, website_pdf, website_concept |
| categories | JSON | Category tags |
| keywords | JSON | English keywords |
| keywords_zh | JSON | Chinese keywords |
| grade_levels | JSON | Applicable grade levels |
| complexity | String(20) | simple, medium, complex |
| subject_area | String(100) | Subject area |
| html_template_path | String(500) | Path to HTML file |
| llm_config | JSON | {provider, model} |
| is_active | Boolean | Template availability |
| usage_count | Integer | Number of times used |

---

## Common Workflows

### Workflow 1: Review Before Adding

```bash
# Step 1: List available demos
python scripts/batch_add_templates.py --document-ids 1,2,3 --list-only

# Step 2: Use interactive script to selectively add
python scripts/add_demos_as_templates.py
```

### Workflow 2: Batch Add with Defaults

```bash
# Add all demos from documents as templates with sensible defaults
python scripts/batch_add_templates.py --document-ids 1,2,3
```

### Workflow 3: Customized Batch Add

```bash
# Add with specific settings
python scripts/batch_add_templates.py \
    --document-ids 1,2,3 \
    --workflow-type ppt_demo \
    --complexity medium \
    --categories "algorithm,visualization" \
    --subject-area "Computer Science"
```

### Workflow 4: Test Before Production

```bash
# Dry run to see what would be added
python scripts/batch_add_templates.py --document-ids 1,2,3 --dry-run
```

---

## Tips

1. **Start with `--list-only`** - Always list demos first to see what's available
2. **Use `--dry-run`** - Preview changes before modifying the database
3. **Use interactive script for first-time setup** - Get familiar with the configuration options
4. **Use batch script for automation** - Once you know your preferred settings
5. **Check existing templates** - Use `--overwrite` flag carefully to avoid duplicates

---

## Verification

After adding templates, verify they're in the database:

```bash
# Using SQLite CLI
sqlite3 learn_your_way.db "SELECT template_id, display_name, workflow_type FROM demo_templates;"

# Using Python
python -c "
from src.core.database import get_db_session
from src.models.demo_template import DemoTemplate
session = next(get_db_session())
templates = session.query(DemoTemplate).all()
for t in templates:
    print(f'{t.template_id:30} | {t.display_name:40} | {t.workflow_type}')
"
```

---

## Script 3: Website Template Creator (PDF/Concept)

**File:** `add_website_as_templates.py`

Interactively review websites from PDF or concept documents and configure them as templates.

### Usage

```bash
cd backend
python scripts/add_website_as_templates.py
```

### Interactive Workflow

1. Enter comma-separated document IDs (e.g., `91,92,93`)
2. The script displays each website with:
   - Document title and ID
   - Type (website_pdf or website_concept)
   - Subject and grade level
   - For concept documents: concept name, overview, mastery points, design idea
   - HTML preview
3. For each website, choose:
   - `a` - Add as template (configure metadata)
   - `s` - Skip this website
   - `q` - Quit
4. If adding, configure template metadata

### Example Session

```
Enter document IDs (comma-separated): 91,92,93

======================================================================
Website #1
======================================================================
📄 Document: 三角函数 (ID: 91)
🔖 Type: website_concept
📚 Subject: 数学
🎓 Grade Level: 12

📖 Concept Information:
   Name: 三角函数
   Overview: 用单位圆在平面直角坐标系上表示三角函数
   Mastery Points: sin cos tan 分别是谁比谁...
   Design Idea: 学生调整角度，直观看到sin cos tan值...

➤ Action? [a=add as template, s=skip, q=quit]: a

Configure as Template
──────────────────────────────────────────────────────────────────

1. template_id (unique identifier) [三角函数]: trig_functions
2. display_name (shown to users) [三角函数]:
...
✅ Created template: trig_functions
✅ HTML saved to: backend/src/templates/website_concept/trig_functions.html
```

---

## Script 4: Batch Website Template Creator

**File:** `batch_add_website_templates.py`

Batch process multiple websites from PDF/concept documents with command-line arguments.

### Basic Usage

```bash
# List all websites from documents
python scripts/batch_add_website_templates.py --document-ids 91,92,93 --list-only

# Add all websites with default settings
python scripts/batch_add_website_templates.py --document-ids 91,92,93

# Dry run (preview without modifying database)
python scripts/batch_add_website_templates.py --document-ids 91,92,93 --dry-run
```

### Advanced Options

```bash
python scripts/batch_add_website_templates.py \
    --document-ids 91,92,93 \
    --complexity medium \
    --categories "math,trigonometry" \
    --subject-area "数学" \
    --grade-levels 10,11,12 \
    --prefix mytemplate \
    --overwrite
```

### Auto-Detection Features

- **Workflow Type**: Automatically detects `website_pdf` vs `website_concept`
- **Categories**: Extracts from concept name or analysis topics
- **Keywords**: Auto-generates from subject and title
- **Chinese Keywords**: Auto-generates from document title

---

## Troubleshooting

### "Document not found"
- **For PPT demos**: Check that the document ID exists in `ppt_documents` table
- **For PDF/Concept websites**: Check that the document ID exists in `documents` table
- Verify the document has been processed (status = "ready")

### "No demos found" (PPT)
- Ensure the document has `slides_data` with `needs_demo: true`
- Check that `demo_html` field is populated for slides

### "No websites found" (PDF/Concept)
- Ensure the document has `processing_results` with `website` key
- Check that the website HTML is not empty
- For concept documents, verify `concept_data` exists if expecting `website_concept` type

### "Template already exists"
- Use `--overwrite` flag in batch mode to update existing templates
- The interactive script will ask if you want to update

### Import errors
- Run from the `backend` directory: `cd backend && python scripts/...`
- Or use: `python -m backend.scripts.batch_add_templates`
