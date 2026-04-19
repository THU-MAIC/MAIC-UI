# Backend Modifications for GLM-4.6 Website Generation

## Overview
Modified the backend logic of website generation to use GLM-4.6, a text-based LLM, focusing on procedural knowledge demonstration with reduced context requirements.

## Key Changes Made

### 1. Content Analysis Focus (`backend/src/services/ai_processor.py:670-718`)
- **Modified**: `_get_content_analysis_prompt()` method in `ZhipuProvider` class
- **Change**: Now focuses on extracting 2-3 key procedural concepts (程序性知识) instead of comprehensive analysis
- **Addition**: Added `procedural_concepts` field to JSON output containing:
  - `name`: Procedural concept name
  - `description`: Brief description
  - `key_steps`: Step-by-step process
  - `complexity`: Simple/Medium/Complex

### 2. Website Generation Logic (`backend/src/services/ai_processor.py:512-553`)
- **Modified**: `generate_website()` method
- **Change**: Extracts procedural concepts from analysis and passes them (not PDF images) to sub-functions
- **Limitation**: Enforces 2-3 procedural concepts limit as requested
- **Fallback**: Creates procedural concepts from key_concepts if none available

### 3. HTML Content Generation (`backend/src/services/ai_processor.py:555-625`)
- **Modified**: `_generate_html_content()` method signature and implementation
- **Change**: Now accepts `procedural_concepts` instead of `pdf_images`
- **Method**: Uses one-shot prompting with reference to `gemini_example_ui.html`
- **Focus**: Creates interactive demonstrations of procedural knowledge
- **No Images**: No longer processes PDF images, reducing context requirements

### 4. Interactive Elements Generation (`backend/src/services/ai_processor.py:627-723`)
- **Modified**: `_generate_metadata_and_interactive()` method
- **Change**: Now generates assessments focused on procedural knowledge understanding
- **Quiz Types**:
  - Step-based multiple choice questions
  - Sequence ordering questions
  - Application scenario analysis
  - Procedural vocabulary definitions
- **No Images**: Removed PDF image processing

### 5. Fallback Analysis (`backend/src/services/ai_processor.py:967-992`)
- **Modified**: `_generate_fallback_analysis()` method
- **Addition**: Added sample procedural concepts for fallback scenarios

## Technical Architecture

### Input Flow
```
PDF Images → Content Analysis → Extract 2-3 Procedural Concepts → GLM-4.6 Generation
```

### Output Structure
- **HTML**: Interactive learning demonstrations (left input, right output layout)
- **Metadata**: Learning objectives and time estimates
- **Interactive Elements**: Procedural knowledge assessments

### Key Features
1. **Reduced Context**: Only 2-3 procedural concepts + user preferences
2. **Text-Based**: No PDF image processing for generation
3. **Interactive**: User input → processing → visual feedback
4. **Assessment-Focused**: Quizzes check procedural understanding
5. **One-Shot**: Uses gemini_example_ui.html as reference

## Benefits of Changes
- **Lower Token Usage**: Reduced from 15-20 images to 2-3 text concepts
- **GLM-4.6 Compatible**: Text-only processing suitable for pure text LLM
- **Focused Learning**: Emphasizes procedural knowledge demonstration
- **Interactive Experience**: Hands-on learning with immediate feedback
- **Scalable**: Can handle larger PDFs by focusing on key procedures

## Usage Example
```python
# Mock analysis with procedural concepts
analysis = {
    "procedural_concepts": [
        {
            "name": "词法分析过程",
            "description": "将源代码转换为Token序列",
            "key_steps": ["读取字符", "匹配模式", "生成Token"],
            "complexity": "中等"
        }
    ]
}

# Generate website
result = await provider.generate_website([], analysis, user_preferences)
```

## Testing
Created `test_modified_generation.py` to verify the modified implementation works correctly with procedural concepts.