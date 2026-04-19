"""
Interactive Components Module

This module provides pre-built interactive component templates for Heavy Mode generation.
These include simulations, quizzes, and other interactive elements.


Date: 2025-01-15
"""

INTERACTIVE_COMPONENTS = {
    "SimulationCanvas": {
        "name": "SimulationCanvas",
        "category": "interactive",
        "description": "Configurable canvas for physics/chemistry/math simulations",
        "simulation_types": {
            "pendulum": {
                "name": "单摆实验",
                "template": """
<div class="pendulum-simulation">
    <canvas id="pendulumCanvas" width="400" height="300" class="w-full border rounded-xl bg-white"></canvas>
    <div class="controls mt-4 space-y-3">
        <div class="control-group">
            <label class="block text-sm font-medium text-gray-700 mb-1">摆长 (Length)</label>
            <input type="range" id="lengthSlider" min="50" max="200" value="100" class="w-full">
            <span id="lengthValue" class="text-sm text-gray-600">100 cm</span>
        </div>
        <div class="control-group">
            <label class="block text-sm font-medium text-gray-700 mb-1">重力加速度 (Gravity)</label>
            <input type="range" id="gravitySlider" min="1" max="20" value="9.8" step="0.1" class="w-full">
            <span id="gravityValue" class="text-sm text-gray-600">9.8 m/s²</span>
        </div>
        <div class="button-group flex gap-3">
            <button id="startBtn" class="flex-1 bg-green-500 text-white py-2 px-4 rounded-xl hover:bg-green-600">开始实验</button>
            <button id="resetBtn" class="flex-1 bg-gray-500 text-white py-2 px-4 rounded-xl hover:bg-gray-600">重置</button>
        </div>
    </div>
    <div class="observation mt-4 p-3 bg-blue-50 rounded-xl">
        <h4 class="font-semibold text-blue-800 mb-2">观察要点 (Observation)</h4>
        <ul class="text-sm text-blue-700 space-y-1">
            <li>• 摆长越长，周期越长（T ∝ √L）</li>
            <li>• 重力越大，周期越短（T ∝ 1/√g）</li>
            <li>• 周期与摆球质量无关</li>
        </ul>
    </div>
</div>
<script>
// 单摆物理模拟
const canvas = document.getElementById('pendulumCanvas');
const ctx = canvas.getContext('2d');
let angle = Math.PI / 4;
let velocity = 0;
let acceleration = 0;
let length = 100;
let gravity = 9.8;
let running = false;

function draw() {{
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const originX = canvas.width / 2;
    const originY = 20;
    const bobX = originX + length * Math.sin(angle);
    const bobY = originY + length * Math.cos(angle);

    // 绘制绳子
    ctx.beginPath();
    ctx.moveTo(originX, originY);
    ctx.lineTo(bobX, bobY);
    ctx.strokeStyle = '#374151';
    ctx.lineWidth = 2;
    ctx.stroke();

    // 绘制摆球
    ctx.beginPath();
    ctx.arc(bobX, bobY, 15, 0, 2 * Math.PI);
    ctx.fillStyle = '#3B82F6';
    ctx.fill();
    ctx.strokeStyle = '#1E40AF';
    ctx.lineWidth = 2;
    ctx.stroke();

    // 绘制支点
    ctx.beginPath();
    ctx.arc(originX, originY, 5, 0, 2 * Math.PI);
    ctx.fillStyle = '#374151';
    ctx.fill();
}}

function update() {{
    if (!running) return;
    acceleration = (-gravity / length) * Math.sin(angle);
    velocity += acceleration * 0.05;
    angle += velocity * 0.05;
    velocity *= 0.999; // 轻微阻尼
}}

function animate() {{
    update();
    draw();
    requestAnimationFrame(animate);
}}

document.getElementById('startBtn').addEventListener('click', () => {{
    running = !running;
    document.getElementById('startBtn').textContent = running ? '暂停' : '开始实验';
}});

document.getElementById('resetBtn').addEventListener('click', () => {{
    running = false;
    angle = Math.PI / 4;
    velocity = 0;
    document.getElementById('startBtn').textContent = '开始实验';
    draw();
}});

document.getElementById('lengthSlider').addEventListener('input', (e) => {{
    length = parseInt(e.target.value);
    document.getElementById('lengthValue').textContent = length + ' cm';
    draw();
}});

document.getElementById('gravitySlider').addEventListener('input', (e) => {{
    gravity = parseFloat(e.target.value);
    document.getElementById('gravityValue').textContent = gravity + ' m/s²';
}});

draw();
animate();
</script>
""",
                "physics_constraints": {
                    "period_formula": "T = 2π√(L/g)",
                    "energy_conservation": "E = KE + PE = constant",
                    "small_angle_approx": "sin(θ) ≈ θ for θ < 15°"
                }
            },
            "projectile": {
                "name": "抛体运动",
                "template": """
<div class="projectile-simulation">
    <canvas id="projectileCanvas" width="500" height="300" class="w-full border rounded-xl bg-white"></canvas>
    <div class="controls mt-4 grid grid-cols-2 gap-4">
        <div class="control-group">
            <label class="block text-sm font-medium text-gray-700 mb-1">初速度 (v₀)</label>
            <input type="range" id="velocitySlider" min="10" max="100" value="50" class="w-full">
            <span id="velocityValue" class="text-sm text-gray-600">50 m/s</span>
        </div>
        <div class="control-group">
            <label class="block text-sm font-medium text-gray-700 mb-1">发射角度 (θ)</label>
            <input type="range" id="angleSlider" min="0" max="90" value="45" class="w-full">
            <span id="angleValue" class="text-sm text-gray-600">45°</span>
        </div>
        <div class="control-group">
            <label class="block text-sm font-medium text-gray-700 mb-1">重力加速度 (g)</label>
            <input type="range" id="gravitySlider" min="1" max="20" value="9.8" step="0.1" class="w-full">
            <span id="gravityValue" class="text-sm text-gray-600">9.8 m/s²</span>
        </div>
        <div class="control-group">
            <label class="block text-sm font-medium text-gray-700 mb-1">高度 (h₀)</label>
            <input type="range" id="heightSlider" min="0" max="100" value="0" class="w-full">
            <span id="heightValue" class="text-sm text-gray-600">0 m</span>
        </div>
    </div>
    <div class="button-group flex gap-3 mt-4">
        <button id="launchBtn" class="flex-1 bg-red-500 text-white py-2 px-4 rounded-xl hover:bg-red-600">发射</button>
        <button id="resetBtn" class="flex-1 bg-gray-500 text-white py-2 px-4 rounded-xl hover:bg-gray-600">重置</button>
    </div>
    <div class="stats mt-4 p-3 bg-green-50 rounded-xl">
        <div class="grid grid-cols-3 gap-4 text-center">
            <div>
                <div class="text-2xl font-bold text-green-700" id="maxHeight">0 m</div>
                <div class="text-sm text-green-600">最大高度</div>
            </div>
            <div>
                <div class="text-2xl font-bold text-green-700" id="range">0 m</div>
                <div class="text-sm text-green-600">射程</div>
            </div>
            <div>
                <div class="text-2xl font-bold text-green-700" id="flightTime">0 s</div>
                <div class="text-sm text-green-600">飞行时间</div>
            </div>
        </div>
    </div>
</div>
"""
            },
            "graphing": {
                "name": "函数绘图",
                "template": """
<div class="graphing-calculator">
    <canvas id="graphCanvas" width="500" height="400" class="w-full border rounded-xl bg-white"></canvas>
    <div class="controls mt-4">
        <div class="function-input">
            <label class="block text-sm font-medium text-gray-700 mb-1">函数表达式 f(x)</label>
            <input type="text" id="functionInput" value="Math.sin(x)" placeholder="例如: Math.sin(x), x*x, Math.exp(x)"
                   class="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500">
        </div>
        <div class="view-controls mt-3 grid grid-cols-2 gap-4">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">X 最小值</label>
                <input type="number" id="xMin" value="-10" class="w-full px-3 py-2 border rounded-xl">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">X 最大值</label>
                <input type="number" id="xMax" value="10" class="w-full px-3 py-2 border rounded-xl">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Y 最小值</label>
                <input type="number" id="yMin" value="-5" class="w-full px-3 py-2 border rounded-xl">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Y 最大值</label>
                <input type="number" id="yMax" value="5" class="w-full px-3 py-2 border rounded-xl">
            </div>
        </div>
        <button id="plotBtn" class="w-full mt-4 bg-blue-500 text-white py-2 px-4 rounded-xl hover:bg-blue-600">绘制函数</button>
    </div>
</div>
"""
            }
        },
        "props": {
            "type": "pendulum | projectile | graphing",
            "parameters": "array of parameter names",
            "constraints": {
                "physics": "real-world",
                "validation": True
            }
        },
        "chinese_labels": {
            "start": "开始实验",
            "reset": "重置",
            "pause": "暂停",
            "parameter": "参数",
            "observe": "观察现象"
        }
    },

    "QuizCard": {
        "name": "QuizCard",
        "category": "interactive",
        "description": "Multiple choice quiz with immediate feedback",
        "template": """
<div class="quiz-card bg-white rounded-2xl shadow-md p-6 mb-4 border-l-4 border-{primary_color}-500">
    <div class="quiz-header mb-4">
        <span class="inline-block px-3 py-1 bg-{primary_color}-100 text-{primary_color}-700 rounded-full text-sm font-semibold">
            问题 {question_number}
        </span>
        <span class="ml-2 text-sm text-gray-500">{difficulty}</span>
    </div>
    <h3 class="text-lg font-semibold text-gray-800 mb-4">{question}</h3>
    <div class="options space-y-2">
        {options}
        <!-- Single option -->
        <button class="quiz-option w-full text-left px-4 py-3 rounded-xl border-2 border-gray-200 hover:border-{primary_color}-300 hover:bg-{primary_color}-50 transition-all duration-200"
                data-correct="{is_correct}" onclick="checkAnswer(this)">
            <span class="option-label font-semibold text-gray-700">{option_label}.</span>
            <span class="option-text text-gray-600">{option_text}</span>
        </button>
    </div>
    <div class="feedback mt-4 p-4 rounded-xl hidden" id="feedback-{question_id}">
        <div class="feedback-icon text-2xl mb-2">{feedback_icon}</div>
        <p class="feedback-message font-medium">{feedback_text}</p>
        <p class="feedback-explanation text-sm text-gray-600 mt-2">{explanation}</p>
    </div>
</div>
<script>
function checkAnswer(button) {{
    const quizCard = button.closest('.quiz-card');
    const allOptions = quizCard.querySelectorAll('.quiz-option');
    const feedback = quizCard.querySelector('[id^="feedback-"]');
    const isCorrect = button.dataset.correct === 'true';

    allOptions.forEach(opt => {{
        opt.disabled = true;
        if (opt.dataset.correct === 'true') {{
            opt.classList.remove('border-gray-200');
            opt.classList.add('border-green-500', 'bg-green-50');
        }}
    }});

    if (isCorrect) {{
        button.classList.add('border-green-500', 'bg-green-50');
        feedback.classList.remove('hidden');
        feedback.classList.add('bg-green-50');
        feedback.querySelector('.feedback-icon').textContent = '✅';
    }} else {{
        button.classList.add('border-red-500', 'bg-red-50');
        feedback.classList.remove('hidden');
        feedback.classList.add('bg-red-50');
        feedback.querySelector('.feedback-icon').textContent = '❌';
    }}
}}
</script>
""",
        "props": {
            "question": "string",
            "options": "array of {label, text, is_correct}",
            "question_number": "number",
            "difficulty": "string",
            "explanation": "string"
        },
        "chinese_labels": {
            "correct": "回答正确！",
            "incorrect": "再想想看...",
            "try_again": "再试一次",
            "show_explanation": "查看解释"
        }
    },

    "DragDrop": {
        "name": "DragDrop",
        "category": "interactive",
        "description": "Sorting and categorization activities",
        "template": """
<div class="dragdrop-activity">
    <div class="items-pool mb-6 p-4 bg-gray-50 rounded-xl">
        <h4 class="font-semibold text-gray-700 mb-3">拖拽项目</h4>
        <div class="flex flex-wrap gap-3" id="dragItems">
            {drag_items}
        </div>
    </div>
    <div class="target-zones grid grid-cols-1 md:grid-cols-2 gap-4">
        {target_zones}
        <!-- Single target zone -->
        <div class="target-zone p-4 bg-white rounded-xl border-2 border-dashed border-gray-300 min-h-32"
             data-category="{category}">
            <h4 class="font-semibold text-gray-700 mb-3">{category_name}</h4>
            <div class="drop-zone space-y-2"></div>
        </div>
    </div>
    <button id="checkAnswers" class="w-full mt-6 bg-green-500 text-white py-3 px-6 rounded-xl hover:bg-green-600">
        检查答案
    </button>
</div>
"""
    },

    "SliderInput": {
        "name": "SliderInput",
        "category": "interactive",
        "description": "Interactive parameter adjustment",
        "template": """
<div class="slider-input">
    <label class="block text-sm font-medium text-gray-700 mb-2">{label}</label>
    <div class="flex items-center gap-4">
        <input type="range" id="{slider_id}" min="{min}" max="{max}" value="{default}" step="{step}"
               class="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer">
        <span id="{value_id}" class="text-sm font-semibold text-{primary_color}-600 min-w-16 text-right">
            {default} {unit}
        </span>
    </div>
    <div class="flex justify-between text-xs text-gray-500 mt-1">
        <span>{min_label}</span>
        <span>{max_label}</span>
    </div>
</div>
"""
    },

    "ClickableDiagram": {
        "name": "ClickableDiagram",
        "category": "interactive",
        "description": "Hotspot overlays for diagrams",
        "template": """
<div class="clickable-diagram relative">
    <img src="{image_url}" alt="{alt_text}" class="w-full rounded-xl" usemap="#diagram-map">
    <map name="diagram-map">
        {hotspots}
        <!-- Single hotspot -->
        <area shape="{shape}" coords="{coords}" href="#" alt="{label}"
              onclick="showHotspotInfo(event, '{info_id}')" class="hotspot">
    </map>
    <div id="{info_id}" class="hidden absolute bg-white p-4 rounded-xl shadow-lg border-l-4 border-{primary_color}-500 max-w-xs">
        <h4 class="font-bold text-gray-800">{label}</h4>
        <p class="text-sm text-gray-600">{description}</p>
    </div>
</div>
<script>
function showHotspotInfo(event, infoId) {{
    event.preventDefault();
    const info = document.getElementById(infoId);
    info.classList.toggle('hidden');
    // Position info near click
    info.style.left = event.pageX + 'px';
    info.style.top = event.pageY + 'px';
}}
</script>
"""
    }
}

# Simulation physics constraints for validation
PHYSICS_CONSTRAINTS = {
    "pendulum": {
        "period": "T = 2π√(L/g)",
        "energy": "E = mgh + ½mv² = constant",
        "max_angle": "Small angle approximation valid for θ < 15°"
    },
    "projectile": {
        "range": "R = (v₀²sin(2θ))/g",
        "max_height": "H = (v₀sin(θ))²/(2g)",
        "time": "t = 2v₀sin(θ)/g"
    },
    "circuit": {
        "ohms_law": "V = IR",
        "power": "P = VI = I²R = V²/R",
        "kirchhoff": "ΣV = 0, ΣI = 0"
    }
}

# Bloom's taxonomy levels for quiz difficulty
BLOOMS_LEVELS = {
    "remember": "记忆 - 回忆基本事实和概念",
    "understand": "理解 - 解释观点或概念",
    "apply": "应用 - 在新情境中运用信息",
    "analyze": "分析 - 发现观点之间的联系",
    "evaluate": "评价 - 证明立场或决定的合理性",
    "create": "创造 - 产生新的或原创的作品"
}
