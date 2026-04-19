import json
from typing import Dict, List

"""Prompt templates used by AI providers.

This module centralizes all long-form prompt strings so provider
implementations can stay lean. Functions return formatted prompt text.
"""

# --------------------------- English provider ---------------------------

def english_content_analysis_prompt(grade_level: str, interests: List[str]) -> str:
    interests_text = ", ".join(interests) if interests else "General learning"
    return f"""
        Analyze these educational PDF pages and provide comprehensive content analysis.

        User Profile:
        - Grade Level: {grade_level}
        - Interests: {interests_text}

        Please provide:
        1. Main topics and subjects covered
        2. Key concepts and terminology
        3. Learning objectives
        4. Prerequisite knowledge points students should already know
        5. Content difficulty assessment
        6. Target grade level recommendation
        7. Content structure (sections, chapters)
        8. Notable visual elements, diagrams, or charts

        Format your response as JSON:
        {{
            "main_topics": ["topic1", "topic2"],
            "key_concepts": ["concept1", "concept2", "concept3"],
            "learning_objectives": ["objective1", "objective2"],
            "prerequisite_knowledge": ["prereq1", "prereq2"],
            "difficulty_level": "beginner/intermediate/advanced",
            "target_grade_level": "K-12 grade level",
            "content_structure": [
                {{
                    "title": "Section Title",
                    "page_start": 1,
                    "page_end": 3,
                    "topics": ["subtopic1", "subtopic2"]
                }}
            ],
            "visual_elements": ["diagrams", "charts", "illustrations"],
            "subject_area": "Mathematics/Science/Language Arts/etc"
        }}
        """


def english_knowledge_card_prompt(analysis: Dict) -> str:
    return f"""
        Generate knowledge cards to help students quickly review prerequisite knowledge.

        Requirements:
        1) One card per prerequisite knowledge point.
        2) Each card includes: title + Markdown summary.
        3) Markdown may include LaTeX formulas, bullet lists, short examples, key definitions.
        4) Keep language concise and suitable for quick review.
        5) Each card should be 4-8 lines, avoid being too long.
        6) If multiple points, sort by importance.
        7) Output JSON only, no extra text.

        Input:
        - Subject: {analysis.get('subject_area', '')}
        - Main topics: {analysis.get('main_topics', [])}
        - Key concepts: {analysis.get('key_concepts', [])}
        - Prerequisite knowledge: {analysis.get('prerequisite_knowledge', [])}
        - Difficulty: {analysis.get('difficulty_level', '')}

        Output format:
        {{
            "cards": [
                {{
                    "title": "Knowledge Point Title",
                    "summary_md": "Markdown content"
                }}
            ]
        }}
        """


def english_website_generation_prompt(
    grade_level: int,
    interests: List[str],
    analysis: Dict
) -> str:
    interests_text = ", ".join(interests) if interests else "General learning"
    topics_text = ", ".join(analysis.get('main_topics', []))
    return f"""
        Create an interactive learning website from these educational PDF pages. Generate a complete,
        self-contained HTML file with embedded CSS and JavaScript.

        User Profile:
        - Grade Level: {grade_level} (adapt content appropriately)
        - Interests: {interests_text}
        - Learning Style: Interactive and visual

        Content Analysis:
        - Subject: {analysis.get('subject_area', 'General Education')}
        - Topics: {topics_text}
        - Difficulty: {analysis.get('difficulty_level', 'intermediate')}

        Requirements:
        1. Create a modern, responsive design using Tailwind CSS
        2. Include the actual PDF page images as content
        3. Add interactive elements:
           - Embedded quizzes based on content
           - Expandable explanations
           - Interactive vocabulary (hover definitions)
           - Progress tracking
        4. Personalize examples based on interests: {interests}
        5. Include navigation between pages/sections
        6. Add learning activities and exercises
        7. Make it age-appropriate for grade {grade_level}

        Structure the response as JSON:
        {{
            "html": "<!DOCTYPE html>...</html>",
            "metadata": {{
                "title": "Interactive [Subject] Learning",
                "subject": "{analysis.get('subject_area', 'Education')}",
                "grade_level": {grade_level},
                "estimated_time_minutes": 45,
                "learning_objectives": ["obj1", "obj2"]
            }},
            "interactive_elements": [
                {{
                    "type": "quiz",
                    "page": 1,
                    "question": "What concept is shown in this image?",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": 0,
                    "explanation": "This concept represents..."
                }},
                {{
                    "type": "vocabulary",
                    "word": "Important term",
                    "definition": "Clear definition for students"
                }}
            ]
        }}
        """


# --------------------------- Anthropic provider ---------------------------

def anthropic_content_analysis_prompt(grade_level: str, interests: List[str]) -> str:
    interests_text = ", ".join(interests) if interests else "综合学习"
    return f"""
        请分析这些教育PDF页面，专门提取程序性知识（即"如何做"的知识）。

        用户画像:
        - 年级: {grade_level}
        - 兴趣: {interests_text}

        请重点关注：
        1. 程序性知识：包含步骤、流程、操作方法的"如何做"内容
        2. 关键概念：支撑这些程序性知识的核心概念
        3. 实践技能：需要通过练习掌握的操作技能
        4. 前置知识点：学习这些流程前需要掌握的基础知识

        请只回复JSON格式:
        {{
            "main_topics": ["主题1", "主题2"],
            "key_concepts": ["概念1", "概念2"],
            "learning_objectives": ["目标1", "目标2"],
            "prerequisite_knowledge": ["前置1", "前置2"],
            "difficulty_level": "初级/中级/高级",
            "target_grade_level": "K-12年级",
            "subject_area": "数学/科学/语言艺术等",
            "procedural_concepts": [
                {{
                    "name": "程序性概念名称",
                    "description": "描述",
                    "key_steps": ["步骤1", "步骤2"],
                    "complexity": "简单/中等/复杂"
                }}
            ]
        }}
        """


def anthropic_knowledge_card_prompt(analysis: Dict) -> str:
    return f"""
        请根据下列内容分析结果，为"前置知识点"生成知识卡片，帮助学生快速回顾与理解。
        要求：
        1) 每个知识点生成一张卡片；
        2) 每张卡片包含：标题 + Markdown 摘要；
        3) Markdown 允许包含公式（LaTeX 语法）、列表、简短示例、关键定义；
        4) 语言简洁、适合学生快速复习；
        5) 每张卡片 4-8 行，避免过长；
        6) 只输出 JSON，不要额外解释。

        输入信息：
        - 学科/主题：{analysis.get('subject_area', '')}
        - 主要主题：{analysis.get('main_topics', [])}
        - 关键概念：{analysis.get('key_concepts', [])}
        - 前置知识点：{analysis.get('prerequisite_knowledge', [])}
        - 难度：{analysis.get('difficulty_level', '')}

        输出格式：
        {{
            "cards": [
                {{
                    "title": "知识点名称",
                    "summary_md": "Markdown 内容"
                }}
            ]
        }}
        """


def anthropic_scientific_prompt(concept_data: Dict) -> str:
    return f"""
作为科学教育专家，请对以下知识点进行严谨的科学建模。

知识点：{concept_data.get('concept_name', '')}
科目：{concept_data.get('subject', '')}
知识点概述：{concept_data.get('concept_overview', '')}
学生掌握要点：{concept_data.get('mastery_points', '')}
设计思路：{concept_data.get('design_idea', '')}

任务：
1. 列出该知识点涉及的核心公式、定律、概念或逻辑规则
2. 明确具体的物理/逻辑机制
3. 列出严禁的科学性错误

请以结构化的 JSON 格式输出：
{{
    "core_formulas": ["公式1"],
    "mechanism": ["机制1"],
    "constraints": ["约束1"],
    "forbidden_errors": ["错误1"],
}}

请按照上述格式严格输出 JSON，不要添加额外解释。
"""


def anthropic_concept_html_prompt(concept_data: Dict, constraints_summary: str) -> str:
    return f"""
创建一个简洁的交互式学习网站，重点突出可视化交互。

【核心知识点】
{concept_data.get('concept_name', '')} - {concept_data.get('subject', '')}
【关键科学约束】
{constraints_summary}

【交互组件要求】
{concept_data.get('design_idea', '')}

【页面设计要求】
1. 完整 HTML 文档，Tailwind CSS 简洁设计
2. 以可视化为主，文字精简
3. JavaScript 严格遵守科学约束
4. 数学公式使用标准 LaTeX 格式：行内用 \\(公式\\)，块级用 \\[公式\\]

【关键 - 必须遵守】
- JavaScript 物理逻辑必须严格符合"工作原理"
- 严禁出现任何"严禁"列表中的错误
- 在 JavaScript 字符串中生成 LaTeX 公式时，必须使用双反斜杠转义！

请直接返回完整的 HTML 代码。
"""


def anthropic_modify_ui_prompt(original_html: str, user_prompt: str, document_context: Dict) -> str:
    return f"""
你是一个UI/UX专家。请根据用户的要求修改提供的交互式学习网站HTML代码，同时尽量保留所有教育内容和功能。

文档信息:
- 标题: {document_context.get('title', '学习网站')}
- 学科: {document_context.get('subject', '教育')}
- 年级: {document_context.get('grade_level', '未指定')}

用户的修改要求: {user_prompt}

原始HTML代码:
{original_html[:200000]}

指示:
1. 分析用户的要求和当前HTML结构
2. 根据用户的需求相应地修改UI，同时保持响应式设计
3. 返回修改后的完整HTML

请直接返回修改后的HTML代码，不要包含其他解释。
"""


def anthropic_procedural_html_prompt(
    procedural_concepts: List[Dict],
    grade_level: str,
    interests: List[str],
    user_instruction: str
) -> str:
    interests_text = ", ".join(interests) if interests else "综合学习"
    concepts_text = json.dumps(procedural_concepts, ensure_ascii=False, indent=2)
    return f"""
请创建一个交互式学习网站来演示程序性知识。

程序性概念：
{concepts_text}

用户画像：
- 年级: {grade_level}
- 兴趣: {interests_text}

用户的特殊需求:
{user_instruction}

要求：
1. 创建完整的HTML文档，包含<!DOCTYPE html>到</html>
2. 使用Tailwind CSS (通过CDN)
3. 实现交互功能：用户输入 -> 处理 -> 输出反馈
4. 为每个程序性概念创建可视化演示
5. 包含步骤指导和学习提示
6. 适合{grade_level}年级学生理解和使用

请只返回HTML代码，不要包含其他解释。
"""


def anthropic_procedural_metadata_prompt(
    procedural_concepts: List[Dict],
    analysis: Dict,
    grade_level: str
) -> str:
    concepts_text = json.dumps(procedural_concepts, ensure_ascii=False, indent=2)
    topics = ", ".join(analysis.get('main_topics', []))
    return f"""
请为程序性知识学习网站生成元数据和交互式测验元素。

程序性概念：
{concepts_text}

内容分析：
- 学科: {analysis.get('subject_area', '综合教育')}
- 主题: {topics}

请只回复JSON格式:
{{
    "metadata": {{
        "title": "网站标题",
        "subject": "学科",
        "grade_level": "{grade_level}",
        "estimated_time_minutes": 30,
        "learning_objectives": ["目标1", "目标2"]
    }},
    "interactive_elements": [
        {{
            "type": "quiz",
            "question": "问题",
            "options": ["A", "B", "C", "D"],
            "correct_answer": 0,
            "explanation": "解释"
        }}
    ]
}}
"""


# --------------------------- Visual engine ---------------------------

def visual_engine_prompt(concept_data: Dict, constraints_summary: str, grade_level: str) -> str:
    return f"""
创建一个简洁的交互式学习网站，重点突出可视化交互。

【核心知识点】
{concept_data.get('concept_name', '')} - {concept_data.get('subject', '')}
【关键科学约束】
{constraints_summary}

【交互组件要求】
{concept_data.get('design_idea', '')}

【页面设计要求】
1. 完整 HTML 文档，Tailwind CSS 简洁设计
2. 以可视化为主，文字精简
3. JavaScript 严格遵守科学约束
4. 数学公式使用标准 LaTeX 格式：行内用 \\(公式\\)，块级用 \\[公式\\]

【关键 - 必须遵守】
- JavaScript 物理逻辑必须严格符合"工作原理"
- 严禁出现任何"严禁"列表中的错误
- 实现所有"验证检查"中的验证点
- 在 JavaScript 字符串中生成 LaTeX 公式时，必须使用双反斜杠转义！
  例如：应写成 "const t = '公式 \\\\ ( x \\\\)'"，而不是 "const t = '公式 \\( x \\)'"。
  这是为了确保反斜杠能正确输出到 HTML 中供渲染引擎识别。

请直接返回完整的 HTML 代码。
"""


# --------------------------- Zhipu provider ---------------------------

def zhipu_content_analysis_prompt(grade_level: str, interests: List[str]) -> str:
    interests_text = ", ".join(interests) if interests else "综合学习"
    return f"""
        请分析这些教育PDF页面，专门提取程序性知识（即"如何做"的知识）。

        用户画像:
        - 年级: {grade_level}
        - 兴趣: {interests_text}

        请重点关注：
        1. 程序性知识：包含步骤、流程、操作方法的"如何做"内容
        2. 关键概念：支撑这些程序性知识的核心概念
        3. 实践技能：需要通过练习掌握的操作技能
        4. 前置知识点：学习这些流程前需要掌握的基础知识

        请提取2-3个最重要的程序性概念，这些应该是学习者需要理解并能够执行的具体流程或步骤。

        请只回复JSON格式:
        {{
            "main_topics": ["主题1", "主题2"],
            "key_concepts": ["概念1", "概念2", "概念3"],
            "learning_objectives": ["目标1", "目标2"],
            "prerequisite_knowledge": ["前置1", "前置2"],
            "difficulty_level": "初级/中级/高级",
            "target_grade_level": "K-12年级",
            "content_structure": [
                {{
                    "title": "章节标题",
                    "page_start": 1,
                    "page_end": 3,
                    "topics": ["子主题1", "子主题2"]
                }}
            ],
            "visual_elements": ["图表", "插图", "图片"],
            "subject_area": "数学/科学/语言艺术等",
            "procedural_concepts": [
                {{
                    "name": "程序性概念名称",
                    "description": "简要描述这个程序性概念是什么",
                    "key_steps": ["步骤1", "步骤2", "步骤3"],
                    "complexity": "简单/中等/复杂"
                }},
                {{
                    "name": "第二个程序性概念",
                    "description": "描述",
                    "key_steps": ["步骤1", "步骤2", "步骤3"],
                    "complexity": "简单/中等/复杂"
                }}
            ]
        }}
        """


def zhipu_knowledge_card_prompt(analysis: Dict) -> str:
    return f"""
        请根据下列内容分析结果，为“前置知识点”生成知识卡片，帮助学生快速回顾与理解。
        要求：
        1) 每个知识点生成一张卡片；
        2) 每张卡片包含：标题 + Markdown 摘要；
        3) Markdown 允许包含公式（LaTeX 语法）、列表、简短示例、关键定义；
        4) 语言简洁、适合学生快速复习；
        5) 每张卡片 4-8 行，避免过长；
        6) 若存在多个知识点，请按重要性排序；
        7) 只输出 JSON，不要额外解释。

        输入信息：
        - 学科/主题：{analysis.get('subject_area', '')}
        - 主要主题：{analysis.get('main_topics', [])}
        - 关键概念：{analysis.get('key_concepts', [])}
        - 前置知识点：{analysis.get('prerequisite_knowledge', [])}
        - 难度：{analysis.get('difficulty_level', '')}

        输出格式：
        {{
            "cards": [
                {{
                    "title": "知识点名称",
                    "summary_md": "Markdown 内容"
                }}
            ]
        }}
        """


def zhipu_html_generation_prompt(grade_level: int, interests: List[str], analysis: Dict) -> str:
    interests_text = ", ".join(interests) if interests else "综合学习"
    topics = ", ".join(analysis.get('main_topics', []))
    return f"""
        请创建一个完整的交互式学习网站的HTML代码，帮助{grade_level}年级学生理解学习内容。

        用户画像:
        - 年级: {grade_level}
        - 兴趣: {interests_text}
        - 学习风格: 交互式和视觉化

        内容分析:
        - 学科: {analysis.get('subject_area', '综合教育')}
        - 主题: {topics}
        - 核心概念: {topics}
        - 难度: {analysis.get('difficulty_level', '中级')}

        HTML要求:
        1. 生成完整的HTML文档，包含<!DOCTYPE html>到</html>
        2. 使用Tailwind CSS (通过CDN: <script src="https://cdn.tailwindcss.com"></script>)
        3. 创建现代化、响应式设计
        4. 包含主要部分: 头部、导航、主内容区、互动元素
        5. 在主内容区要把输入的图片中需要学习的内容转成一个详细的教学网站，根据用户画像个性化传授内容和示例，最好有一些直观的思维导图、流程图、概念关系图谱等视觉元素
        6. 添加JavaScript交互功能

        请只返回HTML代码，不要包含其他解释。
        """


def zhipu_metadata_generation_prompt(grade_level: int, interests: List[str], analysis: Dict) -> str:
    interests_text = ", ".join(interests) if interests else "综合学习"
    topics = ", ".join(analysis.get('main_topics', []))
    key_concepts = ", ".join(analysis.get('key_concepts', []))
    return f"""
        请为学习网站生成元数据和交互元素。

        用户画像:
        - 年级: {grade_level}
        - 兴趣: {interests_text}

        内容分析:
        - 学科: {analysis.get('subject_area', '综合教育')}
        - 主题: {topics}
        - 关键概念: {key_concepts}
        - 难度: {analysis.get('difficulty_level', '中级')}

        请生成以下内容:

        1. 元数据(metadata):
           - title: 适合{grade_level}年级的学习标题
           - subject: 学科名称
           - grade_level: 年级水平
           - estimated_time_minutes: 预计学习时间(30-60分钟)
           - learning_objectives: 2-4个学习目标

        2. 交互元素(interactive_elements):
           - 生成3-5个交互元素，包括:
             * quiz: 选择题，包含问题、选项、正确答案、解释
             * vocabulary: 重要词汇和定义
             * activity: 学习活动或练习

        请只回复JSON格式:
        {{
            "metadata": {{
                "title": "网站标题",
                "subject": "学科",
                "grade_level": {grade_level},
                "estimated_time_minutes": 45,
                "learning_objectives": ["目标1", "目标2", "目标3"]
            }},
            "interactive_elements": [
                {{
                    "type": "quiz",
                    "question": "问题内容",
                    "options": ["选项A", "选项B", "选项C", "选项D"],
                    "correct_answer": 0,
                    "explanation": "答案解释"
                }},
                {{
                    "type": "vocabulary",
                    "word": "重要术语",
                    "definition": "术语定义"
                }}
            ]
        }}
        """


def zhipu_modify_ui_prompt(original_html: str, user_prompt: str, document_context: Dict) -> str:
    return f"""
你是一个UI/UX专家。请根据用户的要求修改提供的交互式学习网站HTML代码，同时尽量保留所有教育内容和功能。

文档信息:
- 标题: {document_context.get('title', '学习网站')}
- 学科: {document_context.get('subject', '教育')}
- 年级: {document_context.get('grade_level', '未指定')}
- 主要主题: {', '.join(document_context.get('analysis', {}).get('main_topics', []))}
- 关键概念: {', '.join(document_context.get('analysis', {}).get('key_concepts', []))}

用户的修改要求: {user_prompt}

原始HTML代码:
{original_html[:200000]}

指示:
1. 分析用户的要求和当前HTML结构
2. 根据用户的需求相应地修改UI，同时保持响应式设计
3. 返回修改后的完整HTML

请直接返回修改后的HTML代码，不要包含其他解释。
"""


def zhipu_one_shot_html_prompt(
    procedural_concepts: List[Dict],
    grade_level: str,
    interests: List[str],
    user_instruction: str
) -> str:
    interests_text = ", ".join(interests) if interests else "综合学习"
    concepts_text = json.dumps(procedural_concepts, ensure_ascii=False, indent=2)
    return f"""
请创建一个交互式学习网站来演示程序性知识，参考以下示例：

示例网站结构（来自 Compiler Explorer: Lexical Analysis）：
- 分为左右两栏布局
- 左侧：输入区域，用户可以进行实践操作
- 右侧：输出区域，实时显示处理结果
- 包含清晰的步骤说明和视觉反馈

现在请为以下程序性概念创建类似的学习网站：

程序性概念：
{concepts_text}

用户画像：
- 年级: {grade_level}
- 兴趣: {interests_text}

用户的特殊需求: 
{user_instruction}

要求：
1. 创建完整的HTML文档，包含<!DOCTYPE html>到</html>
2. 使用现代化CSS样式（类似示例的深色主题）
3. 实现交互功能：用户输入 -> 处理 -> 输出反馈
4. 为每个程序性概念创建可视化演示
5. 包含步骤指导和学习提示
6. 适合{grade_level}年级学生理解和使用

请只返回HTML代码，不要包含其他解释。
"""


def zhipu_procedural_metadata_prompt(
    procedural_concepts: List[Dict],
    analysis: Dict,
    grade_level: str,
    interests: List[str]
) -> str:
    interests_text = ", ".join(interests) if interests else "综合学习"
    concepts_text = json.dumps(procedural_concepts, ensure_ascii=False, indent=2)
    topics = ", ".join(analysis.get('main_topics', []))
    key_concepts = ", ".join(analysis.get('key_concepts', []))
    return f"""
请为程序性知识学习网站生成元数据和交互式测验元素。

程序性概念：
{concepts_text}

用户画像：
- 年级: {grade_level}
- 兴趣: {interests_text}

内容分析：
- 学科: {analysis.get('subject_area', '综合教育')}
- 主题: {topics}
- 关键概念: {key_concepts}

请生成以下内容：

1. 元数据(metadata):
   - title: 适合{grade_level}年级的程序性知识学习标题
   - subject: 学科名称
   - grade_level: 年级水平
   - estimated_time_minutes: 预计学习时间(20-40分钟)
   - learning_objectives: 2-4个程序性学习目标

2. 交互元素(interactive_elements):
   - 生成3-5个测验题目，专门检查学生对程序性知识的理解：
     * quiz: 针对程序步骤的选择题
     * quiz: 识别正确顺序的排序题
     * quiz: 应用场景分析题
     * vocabulary: 程序性相关术语定义

请只回复JSON格式:
{{
    "metadata": {{
        "title": "网站标题",
        "subject": "学科",
        "grade_level": {grade_level},
        "estimated_time_minutes": 30,
        "learning_objectives": ["目标1", "目标2", "目标3"]
    }},
    "interactive_elements": [
        {{
            "type": "quiz",
            "question": "关于程序性问题",
            "options": ["选项A", "选项B", "选项C", "选项D"],
            "correct_answer": 0,
            "explanation": "答案解释"
        }},
        {{
            "type": "vocabulary",
            "word": "程序性术语",
            "definition": "术语定义"
        }}
    ]
}}
"""
