"""
Simulation Validator Module

This module provides validation functions for physics/chemistry/math simulations.
Ensures simulations follow real-world laws and constraints.


Date: 2025-01-15
"""

import re
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


class SimulationValidator:
    """Validates scientific accuracy of simulations."""

    def __init__(self):
        """Initialize the simulation validator."""
        # Physical constants
        self.constants = {
            'gravity': 9.8,  # m/s²
            'speed_of_light': 299792458,  # m/s
            'planck': 6.626e-34,  # J·s
            'avogadro': 6.022e23,  # mol⁻¹
            'gas_constant': 8.314,  # J/(mol·K)
        }

        # Physics formulas for validation
        self.formulas = {
            'pendulum_period': 'T = 2π√(L/g)',
            'projectile_range': 'R = (v₀²sin(2θ))/g',
            'projectile_max_height': 'H = (v₀sin(θ))²/(2g)',
            'kinetic_energy': 'KE = ½mv²',
            'potential_energy': 'PE = mgh',
            'force': 'F = ma',
            'ohms_law': 'V = IR',
            'power': 'P = VI'
        }

    def validate_physics(self, sim_code: str, sim_type: str) -> Tuple[bool, List[str]]:
        """
        Validate physics simulation code.

        Args:
            sim_code: JavaScript code for simulation
            sim_type: Type of simulation (pendulum, projectile, etc.)

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        if sim_type == 'pendulum':
            issues.extend(self._validate_pendulum(sim_code))
        elif sim_type == 'projectile':
            issues.extend(self._validate_projectile(sim_code))
        elif sim_type == 'circuit':
            issues.extend(self._validate_circuit(sim_code))
        else:
            issues.append("建议：添加针对该模拟类型的验证规则")

        # General physics validation
        issues.extend(self._validate_energy_conservation(sim_code))
        issues.extend(self._validate_units(sim_code))

        is_valid = not any(i.startswith("错误") for i in issues)
        return is_valid, issues

    def _validate_pendulum(self, code: str) -> List[str]:
        """Validate pendulum simulation physics."""
        issues = []

        # Check for period formula
        if 'Math.PI' not in code and 'Math.PI' not in code:
            issues.append("警告：单摆周期公式应使用 π (Math.PI)")

        # Check for gravity constant
        if 'gravity' not in code and 'g ' not in code:
            issues.append("警告：单摆模拟应包含重力加速度参数")

        # Check for length parameter
        if 'length' not in code:
            issues.append("警告：单摆模拟应包含摆长参数")

        # Check for reasonable gravity value
        gravity_match = re.search(r'gravity\s*[=:]\s*([0-9.]+)', code)
        if gravity_match:
            gravity_value = float(gravity_match.group(1))
            if gravity_value < 1 or gravity_value > 20:
                issues.append(f"警告：重力加速度值 {gravity_value} 不在合理范围内 (1-20 m/s²)")

        # Check for small angle approximation or full equation
        if 'Math.sin' not in code:
            issues.append("错误：单摆模拟应使用 sin 函数计算运动")

        return issues

    def _validate_projectile(self, code: str) -> List[str]:
        """Validate projectile motion simulation physics."""
        issues = []

        # Check for velocity components
        if 'velocity' not in code and 'speed' not in code:
            issues.append("警告：抛体运动模拟应包含初速度参数")

        # Check for angle parameter
        if 'angle' not in code:
            issues.append("警告：抛体运动模拟应包含发射角度")

        # Check for gravity
        if 'gravity' not in code:
            issues.append("警告：抛体运动模拟应包含重力加速度")

        # Check for motion equations (should have x and y components)
        if 'x' not in code or 'y' not in code:
            issues.append("警告：抛体运动应分别计算 x 和 y 方向的运动")

        # Check for trigonometric functions for angle decomposition
        if 'Math.cos' not in code or 'Math.sin' not in code:
            issues.append("警告：应使用 cos/sin 分解初速度到 x/y 方向")

        return issues

    def _validate_circuit(self, code: str) -> List[str]:
        """Validate circuit simulation physics."""
        issues = []

        # Check for Ohm's law
        has_voltage = 'voltage' in code or 'V ' in code
        has_current = 'current' in code or 'I ' in code
        has_resistance = 'resistance' in code or 'R ' in code

        if not (has_voltage and has_current and has_resistance):
            issues.append("建议：电路模拟应包含电压、电流和电阻")

        # Check for power calculation
        if 'power' not in code:
            issues.append("建议：添加功率计算 (P = VI)")

        return issues

    def _validate_energy_conservation(self, code: str) -> List[str]:
        """Check for energy conservation principles."""
        issues = []

        # Look for energy-related keywords
        energy_keywords = ['energy', 'kinetic', 'potential', 'conservation', 'KE', 'PE']
        has_energy = any(keyword in code.lower() for keyword in energy_keywords)

        if has_energy:
            # Check for energy conservation
            if 'conservation' not in code.lower():
                issues.append("建议：模拟中提及能量时，应体现能量守恒定律")

        return issues

    def _validate_units(self, code: str) -> List[str]:
        """Check for proper units in comments and labels."""
        issues = []

        # Common physics units
        expected_units = {
            'time': ['s', '秒', 'second'],
            'distance': ['m', '米', 'meter'],
            'velocity': ['m/s', '米/秒'],
            'acceleration': ['m/s²', '米/秒²'],
            'force': ['N', '牛顿'],
            'energy': ['J', '焦耳'],
            'power': ['W', '瓦特']
        }

        # Check for unit labels in the code
        for quantity, units in expected_units.items():
            if quantity in code.lower():
                has_unit = any(unit in code for unit in units)
                if not has_unit:
                    issues.append(f"建议：{quantity} 参数应标注单位 ({', '.join(units)})")

        return issues

    def validate_chemistry(self, sim_code: str) -> Tuple[bool, List[str]]:
        """
        Validate chemistry simulation code.

        Args:
            sim_code: JavaScript code for simulation

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check for molecular accuracy
        if 'atom' in sim_code.lower() or 'molecule' in sim_code.lower():
            # Check for atomic numbers or masses
            if not re.search(r'(atomic|mass|number)', sim_code.lower()):
                issues.append("建议：分子模拟应包含原子质量或原子序数")

        # Check for bond representation
        if 'bond' in sim_code.lower():
            if 'angle' not in sim_code.lower():
                issues.append("建议：化学键模拟应包含键角参数")

        # Check for periodic table references
        if 'element' in sim_code.lower():
            if not re.search(r'(periodic|group|period)', sim_code.lower()):
                issues.append("建议：元素相关模拟应参考周期表")

        return (not any(i.startswith("错误") for i in issues), issues)

    def validate_math(self, sim_code: str) -> Tuple[bool, List[str]]:
        """
        Validate math simulation/code accuracy.

        Args:
            sim_code: JavaScript code for simulation

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check for Math object usage
        math_functions = ['Math.sin', 'Math.cos', 'Math.tan', 'Math.sqrt', 'Math.log', 'Math.exp']
        used_math = any(func in sim_code for func in math_functions)

        if 'graph' in sim_code.lower() or 'plot' in sim_code.lower():
            if not used_math:
                issues.append("建议：绘图函数应使用数学函数（Math.sin, Math.cos等）")

        # Check for canvas or plotting
        if 'canvas' in sim_code.lower():
            if 'getContext' not in sim_code:
                issues.append("错误：Canvas 绘图应使用 getContext 方法")

        # Check for function plotting
        if 'function' in sim_code.lower() or 'f(x)' in sim_code:
            if 'x' not in sim_code or 'y' not in sim_code:
                issues.append("警告：函数绘图应计算 x 和 y 坐标")

        return (not any(i.startswith("错误") for i in issues), issues)

    def validate_interactive_functionality(self, html: str) -> Tuple[bool, List[str]]:
        """
        Validate that interactive elements actually work.

        Args:
            html: Complete HTML string

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check for simulation container
        if 'canvas' not in html.lower():
            issues.append("建议：模拟应使用 canvas 元素进行渲染")

        # Check for control buttons
        if 'button' not in html.lower():
            issues.append("警告：模拟应包含控制按钮（开始、暂停、重置等）")
        else:
            # Check for essential buttons
            button_types = ['开始', 'start', '重置', 'reset', '暂停', 'pause']
            found_buttons = [btn for btn in button_types if btn.lower() in html.lower()]
            if len(found_buttons) < 2:
                issues.append("建议：模拟应至少包含开始和重置按钮")

        # Check for parameter controls
        if 'input' not in html.lower() and 'slider' not in html.lower():
            issues.append("建议：添加参数控制（滑块、输入框）增强交互性")

        # Check for JavaScript error handling
        script_content = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
        if script_content:
            combined_scripts = ' '.join(script_content)
            if 'try' not in combined_scripts and 'catch' not in combined_scripts:
                issues.append("建议：添加 try-catch 错误处理")

        # Check for animation loop
        if 'requestAnimationFrame' not in html:
            issues.append("建议：使用 requestAnimationFrame 实现平滑动画")

        return (not any(i.startswith("错误") for i in issues), issues)

    def get_validation_summary(self, validations: Dict[str, Tuple[bool, List[str]]]) -> Dict:
        """
        Get summary of all simulation validations.

        Args:
            validations: Dict of {validation_type: (is_valid, issues)}

        Returns:
            Summary dict
        """
        all_issues = []
        all_valid = True

        for validation_type, (is_valid, issues) in validations.items():
            if not is_valid:
                all_valid = False
            all_issues.extend([f"[{validation_type}] {issue}" for issue in issues])

        return {
            'overall_valid': all_valid,
            'total_issues': len(all_issues),
            'issues': all_issues,
            'validations_performed': list(validations.keys())
        }
