"""
Heavy Mode Prompt Templates

This module contains prompt templates for the 2-stage Heavy Mode generation pipeline.
Each prompt is optimized for Chinese output and includes validation guidance.

Date: 2025-01-15
"""

# Language requirements for Chinese output
LANGUAGE_REQUIREMENTS_CN = """
**语言要求（重要）：**
- 所有用户可见内容必须使用简体中文
- HTML标签、CSS类名、JavaScript变量名使用英文
- 按钮文本、提示信息、说明文字使用中文
- 测验题目、选项、解释使用中文
- 如需引用英文原文，格式：英文原文（中文译名）
- 使用标准中文标点符号：。，；：！？（）【】

**中文排版规范：**
- 中文字体：'Source Han Sans CN', 'Microsoft YaHei', 'SimHei', sans-serif
- 字号：标题24-32px，正文16px，注释14px
- 行高：1.6-1.8（提升可读性）
- 段落间距：1.5-2em

**输出格式要求（必须）：**
- 仅返回完整HTML文档本体（从<!DOCTYPE html>到</html>）
- 严禁使用Markdown代码围栏
- 不要输出```html、```或任何额外说明文字
"""

# Language requirements for English output
LANGUAGE_REQUIREMENTS_EN = """
**Language Requirements (IMPORTANT):**
- All user-visible content must be in English
- HTML tags, CSS class names, JavaScript variable names should use English
- Button text, prompts, instructions should be in English
- Quiz questions, options, explanations should be in English
- Use standard English punctuation: . , ; : ! ? ( ) [ ]

**English Typography Guidelines:**
- Font: 'Inter', 'Segoe UI', 'Roboto', sans-serif
- Font sizes: Title 24-32px, Body 16px, Notes 14px
- Line height: 1.6-1.8 (for readability)
- Paragraph spacing: 1.5-2em

**Output Format Requirements (MUST):**
- Return only the complete HTML document (from <!DOCTYPE html> to </html>)
- Do NOT use Markdown code fences
- Do NOT output ```html, ``` or any extra explanation text
"""

LANGUAGE_REQUIREMENTS = LANGUAGE_REQUIREMENTS_CN  # Default to Chinese

# Stage 1: Content-Aligned Interactive Simulations
STAGE1_ALIGNED_SIMULATION_PROMPT = """
你是一个专业的交互式教育工具开发专家。你的任务是为程序性知识学习网站创建具有强内容对齐性的交互式模拟。

**核心目标：创建左侧过程展示 + 右侧交互模拟的双栏布局，确保两者高度对齐，帮助学生理解概念。**

程序性概念信息：
{procedural_concepts}

关键概念：
{key_concepts_list}

学习目标：
{learning_objectives}

用户画像：
- 年级: {grade_level}
- 兴趣: {interests}
- 学科: {subject}

**布局架构要求（必须遵循）：**

1. **左右双栏布局（核心设计）**
   ```html
   <div class="simulation-container">
       <!-- 左侧：程序性过程展示 -->
       <div class="process-panel">
           <!-- 过程步骤 -->
       </div>

       <!-- 右侧：交互式模拟 -->
       <div class="simulation-panel">
           <!-- Canvas/SVG模拟 -->
           <!-- 控制面板 -->
       </div>
   </div>
   ```

2. **左侧面板 - 程序性过程展示**
   - 显示步骤编号（步骤1、步骤2、步骤3...）
   - 每个步骤包含：
     * 步骤标题（简洁明确）
     * 步骤说明（使用{grade_level}年级可理解的语言）
     * 当前步骤高亮显示
     * 已完成步骤标记✓
   - 使用垂直流程图或步骤卡片布局
   - 实时更新：当用户在右侧模拟中操作时，左侧自动高亮对应步骤

3. **右侧面板 - 交互式模拟**
   - 使用Canvas API或SVG创建可视化模拟
   - 必须包含的控制元素：
     * 开始/暂停按钮
     * 重置按钮
     * 参数调节滑块（至少2个可调参数）
     * 实时数据显示面板
   - 模拟必须遵循真实的物理/数学/化学定律

**内容对齐要求（最重要）：**

1. **步骤与模拟的同步**
   - 左侧步骤1 → 右侧模拟显示步骤1的现象
   - 左侧步骤2 → 右侧模拟显示步骤2的现象
   - 左侧步骤3 → 右侧模拟显示步骤3的现象

   示例（单摆模拟）：
   - 步骤1: "设置摆长" → 右侧：显示摆长参数调节控件，摆线随调节变化
   - 步骤2: "释放摆球" → 右侧：点击开始，摆球开始摆动
   - 步骤3: "观察周期" → 右侧：实时显示周期数据，与左侧公式对比

2. **视觉对齐技巧**
   - 左侧步骤使用颜色编码（如：蓝色=未完成，绿色=进行中，灰色=已完成）
   - 右侧模拟中的对应元素使用相同的颜色系统
   - 添加连接线或箭头指示步骤与模拟的关系（如适用）

3. **动态反馈机制**
   - 用户操作右侧模拟时，左侧自动跳转到对应步骤
   - 鼠标悬停在左侧步骤时，右侧模拟高亮相关元素
   - 完成步骤后显示鼓励性反馈："太棒了！已完成步骤X"

**学科特定模拟要求：**

**物理模拟：**
- 遵循真实物理定律：T = 2π√(L/g), E = KE + PE = constant
- 重力加速度：g = 9.8 m/s²
- 示例：单摆、抛体运动、弹簧振子、电路仿真

**化学模拟：**
- 准确的原子序数和化学键角度
- 反应平衡和化学计量
- 示例：分子结构、反应过程、酸碱滴定

**数学模拟：**
- 精确的数学计算和函数绘图
- 几何变换的准确性
- 示例：函数图像、几何证明、统计分布

**技术实现要求：**

1. **HTML结构**
   ```html
   <!DOCTYPE html>
   <html lang="zh-CN">
   <head>
       <meta charset="UTF-8">
       <meta name="viewport" content="width=device-width, initial-scale=1.0">
       <title>{subject}交互式学习</title>
       <script src="https://cdn.tailwindcss.com"></script>
   </head>
   <body class="bg-gray-50">
       <header class="bg-white shadow-md p-4">
           <h1 class="text-2xl font-bold text-center">{subject}</h1>
       </header>

       <main class="container mx-auto px-4 py-8">
           <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
               <!-- 左侧：过程面板 -->
               <div class="process-panel bg-white rounded-2xl shadow-lg p-6">
                   <!-- 过程步骤 -->
               </div>

               <!-- 右侧：模拟面板 -->
               <div class="simulation-panel bg-white rounded-2xl shadow-lg p-6">
                   <!-- Canvas + 控件 -->
               </div>
           </div>
       </main>

       <script>
           // 模拟逻辑代码
           // 步骤同步逻辑
           // 动画循环（使用requestAnimationFrame）
       </script>
   </body>
   </html>
   ```

2. **JavaScript功能要求**
   - 事件监听：所有按钮和滑块必须绑定事件处理器
   - 数据更新：实时更新显示数据（周期、速度、位置等）
   - 步骤同步：根据模拟状态更新左侧步骤高亮
   - 错误处理：处理边界情况和无效输入

3. **响应式设计**
   - 桌面端（≥1024px）：左右并排显示
   - 平板/移动端（<1024px）：上下堆叠，模拟在上或下（视内容而定）

**输出要求：**
- 返回完整的、可直接运行的HTML文档
- 所有功能完整实现，无TODO或占位符
- JavaScript无语法错误和逻辑错误
- 中文界面，中文注释
- 包含至少2个可调参数的滑块控件
- 包含开始/暂停/重置三个基本按钮
- 左右面板内容高度对齐，步骤清晰对应

{language_requirements}

请直接返回完整的HTML代码，不要包含其他解释。
"""

# Stage 2: Layout Polish & Visual Refinement
STAGE2_POLISH_PROMPT = """
你是一个UI/UX设计师和前端工程师，负责优化和润色交互式学习网站。

**任务：布局优化和视觉润色，确保HTML可完美渲染且无逻辑错误**

当前HTML：
{html_simulation}

主题配色：
- 主色: #{primary_color}
- 强调色: #{accent_color}
- 学科: {subject}

**优化要求：**

1. **渲染完整性检查**
   - 确保所有HTML标签正确闭合
   - 确保所有JavaScript语法正确，无运行时错误
   - 确保Canvas/SVG元素正确渲染
   - 测试所有按钮和控件功能正常

2. **布局优化**
   - 确保左右两栏在桌面端等高显示
   - 优化间距和padding，使视觉更舒适
   - 确保响应式布局在各种屏幕尺寸下正常工作
   - 移动端优化：触摸目标至少44px，合理的间距

3. **视觉润色**
   - 应用Duolingo风格的设计：
     * 大圆角：rounded-2xl (24px)
     * 柔和阴影：shadow-lg
     * 清晰的色彩对比
   - 主色用于：主要按钮、进度指示、当前步骤高亮
   - 强调色用于：次要按钮、装饰元素、悬停效果
   - 背景使用渐变：from-{{{primary_color}}}-50 to-white
   - 卡片使用纯白背景 + 柔和阴影

4. **交互动效**
   - 按钮：hover:scale-105, active:scale-95
   - 步骤卡片：hover:shadow-xl过渡效果
   - 使用transition-all duration-200实现平滑过渡
   - 加载或计算时显示loading状态（animate-pulse）

5. **中文字体优化**
   - 字体：'Source Han Sans CN', 'Microsoft YaHei', sans-serif
   - 行高：1.6-1.8（提升可读性）
   - 字间距：letter-spacing: 0.01em
   - 段落间距：margin-bottom: 1.5em

6. **可访问性增强**
   - 确保足够的颜色对比度（WCAG AA标准）
   - 为按钮添加清晰的focus状态
   - 为Canvas内容添加aria-label描述
   - 键盘导航支持（Tab键可访问所有控件）

**视觉模式参考：**

使用Duolingo风格的CSS样式：
- 步骤卡片：白色背景、大圆角(1.5rem)、柔和阴影、左侧彩色边框
- 按钮：主色背景、圆角(0.75rem)、悬停放大效果
- 模拟画布：渐变背景、内阴影效果

Tailwind CSS类名示例：
- 卡片：bg-white rounded-2xl shadow-lg p-6
- 按钮：bg-{{{primary_color}}} text-white rounded-xl hover:scale-105
- 渐变背景：bg-gradient-to-br from-gray-50 to-white
- 过渡效果：transition-all duration-200
- 圆角边框：border-l-4 border-{{{accent_color}}}

**错误检查清单：**
- [ ] 所有HTML标签正确闭合
- [ ] JavaScript无语法错误
- [ ] Canvas/SVG正确初始化和渲染
- [ ] 所有事件监听器正确绑定
- [ ] 无console错误或警告
- [ ] 按钮点击有响应
- [ ] 滑块调节有效
- [ ] 动画循环正常运行
- [ ] 数据实时更新显示

**输出要求：**
- 返回完整的、经过优化的HTML文档
- 所有视觉样式已应用
- 所有功能已测试确认正常
- 代码整洁，注释清晰
- 保持原有功能不变，只做视觉和布局优化

{language_requirements}

请直接返回优化后的完整HTML代码，不要包含其他解释。
"""

# Refinement prompts for when validation fails
REFINEMENT_PROMPTS = {
    "stage1_missing_alignment": """
**内容对齐问题：**

左侧过程步骤与右侧模拟之间的对齐不够清晰。

请改进：
1. 为每个步骤添加明确的编号和标题
2. 确保每个步骤在右侧模拟中有对应的视觉反馈
3. 添加颜色编码系统，让用户清楚当前处于哪个步骤
4. 实现步骤自动高亮：当模拟进行时，左侧相应步骤自动高亮

示例改进：
- 步骤1（蓝色高亮）：设置参数 → 右侧显示参数调节面板
- 步骤2（灰色）：开始实验 → 等待用户操作
- 步骤3（灰色）：观察结果 → 实验完成后显示

请修正并返回完整HTML。
""",

    "stage1_simulation_not_working": """
**模拟功能问题：**

模拟的JavaScript代码存在问题，请检查：

1. Canvas初始化
   - 确保在DOMContentLoaded后初始化
   - 检查canvas元素是否正确获取

2. 动画循环
   - 使用requestAnimationFrame而不是setInterval
   - 确保动画循环有正确的停止条件

3. 事件绑定
   - 所有按钮都绑定了click事件
   - 所有滑块都绑定了input事件
   - 事件处理器函数名正确

4. 数据更新
   - 确保数据实时更新到DOM
   - 显示格式正确（保留合理小数位）

示例修正：
```javascript
// 正确的动画循环模式
let animationId;
function animate() {
    updateSimulation();
    drawCanvas();
    updateDataDisplay();
    animationId = requestAnimationFrame(animate);
}

// 正确的开始/停止
function startSimulation() {
    if (!animationId) {
        animate();
    }
}

function stopSimulation() {
    if (animationId) {
        cancelAnimationFrame(animationId);
        animationId = null;
    }
}
```

请修正JavaScript代码并返回完整HTML。
""",

    "stage1_missing_controls": """
**控制元素缺失：**

模拟缺少必要的控制元素。请确保包含：

1. **基本按钮（必须）**
   - 开始按钮
   - 暂停按钮
   - 重置按钮

2. **参数滑块（至少2个）**
   ```html
   <div class="control-group">
       <label>参数1名称: <span id="param1-value">50</span></label>
       <input type="range" id="param1" min="0" max="100" value="50">
   </div>
   ```

3. **数据显示面板**
   ```html
   <div class="data-panel">
       <div>周期: <span id="period">--</span> 秒</div>
       <div>速度: <span id="velocity">--</span> m/s</div>
   </div>
   ```

4. **步骤进度指示**
   ```html
   <div class="progress-indicator">
       <div class="step active" data-step="1">步骤1</div>
       <div class="step" data-step="2">步骤2</div>
       <div class="step" data-step="3">步骤3</div>
   </div>
   ```

请添加所有必要的控制元素并返回完整HTML。
""",

    "stage2_rendering_errors": """
**HTML渲染错误：**

HTML存在渲染问题，请检查并修复：

1. **标签闭合**
   - 检查所有<div>、<span>、<p>等标签是否正确闭合
   - 检查<table>、<ul>、<ol>等结构的完整性

2. **JavaScript错误**
   - 检查是否有未定义的变量或函数
   - 检查是否有语法错误（括号、分号等）
   - 确保所有DOM操作在元素存在后执行

3. **Canvas/SVG渲染**
   - 确保canvas有明确的width和height属性
   - 检查SVG元素的命名空间是否正确

4. **CSS冲突**
   - 检查是否有重复的class或id定义
   - 确保Tailwind类名使用正确

调试建议：
```javascript
// 添加错误处理
window.addEventListener('error', function(e) {
    console.error('JavaScript错误:', e.error);
});

// 在关键位置添加日志
console.log('初始化模拟...');
console.log('Canvas尺寸:', canvas.width, canvas.height);
```

请修复所有错误并返回完整HTML。
""",

    "stage2_visual_inconsistency": """
**视觉一致性问题：**

设计风格不够统一，请改进：

1. **颜色系统统一**
   - 主色用于所有主要交互元素
   - 强调色用于高亮和装饰
   - 背景色统一使用渐变

2. **间距统一**
   - 卡片内边距：p-6 (1.5rem)
   - 卡片间距：gap-6 (1.5rem) 或 space-y-6
   - 元素内边距：p-4 (1rem)

3. **圆角统一**
   - 大卡片：rounded-2xl (24px)
   - 按钮：rounded-xl (12px)
   - 小元素：rounded-lg (8px)

4. **阴影统一**
   - 悬停状态：shadow-lg
   - 默认状态：shadow-md
   - 内嵌元素：shadow-inner

请应用一致的视觉风格并返回完整HTML。
""",

    "stage2_mobile_not_optimized": """
**移动端优化不足：**

移动端体验需要改进，请添加：

1. **响应式布局**
   ```html
   <!-- 桌面：左右并排 -->
   <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
   ```

2. **触摸友好**
   - 按钮最小高度：min-h-[44px]
   - 滑块增大的触摸区域：p-2
   - 增大点击热区

3. **移动端特定优化**
   ```css
   @media (max-width: 768px) {
       .simulation-container {
           flex-direction: column;
       }
       .canvas-container {
           height: 300px;  /* 限制高度 */
       }
   }
   ```

4. **字体大小**
   - 移动端标题：text-xl 而不是 text-3xl
   - 移动端正文：text-base 而不是 text-lg
   - 使用响应式类：text-lg md:text-xl

请优化移动端体验并返回完整HTML。
"""
}

# Helper function to get stage prompt
def get_stage_prompt(stage: int, language: str = 'zh', **kwargs) -> str:
    """
    Get the prompt for a specific stage.

    Args:
        stage: Stage number (1-2)
        language: Language preference ('zh' for Chinese, 'en' for English)
        **kwargs: Variables to format into the prompt

    Returns:
        Formatted prompt string
    """
    prompts = {
        1: STAGE1_ALIGNED_SIMULATION_PROMPT,
        2: STAGE2_POLISH_PROMPT
    }

    base_prompt = prompts.get(stage, "")
    if not base_prompt:
        raise ValueError(f"Invalid stage: {stage}. Must be 1 or 2.")

    # Add language requirements based on user preference
    if language == 'en':
        kwargs['language_requirements'] = LANGUAGE_REQUIREMENTS_EN
    else:
        kwargs['language_requirements'] = LANGUAGE_REQUIREMENTS_CN

    return base_prompt.format(**kwargs)


def get_refinement_prompt(issue_type: str, **kwargs) -> str:
    """
    Get a refinement prompt for a specific validation issue.

    Args:
        issue_type: Type of issue (e.g., 'stage1_missing_alignment')
        **kwargs: Variables to format into the prompt

    Returns:
        Formatted refinement prompt
    """
    prompt = REFINEMENT_PROMPTS.get(issue_type)
    if not prompt:
        return "请修正上述问题并返回完整的HTML代码。"

    return prompt.format(**kwargs)
