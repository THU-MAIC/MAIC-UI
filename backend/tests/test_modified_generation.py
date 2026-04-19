#!/usr/bin/env python3
"""
Test script for the modified GLM-4.6 website generation functionality
"""
import asyncio
import sys
import os

# Add the backend src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.ai_processor import ChineseProvider

async def test_modified_generation():
    """Test the modified website generation with procedural concepts"""

    # Create a mock analysis with procedural concepts
    mock_analysis = {
        "main_topics": ["编译原理", "词法分析"],
        "key_concepts": ["Token", "正则表达式", "有限自动机"],
        "learning_objectives": ["理解词法分析的基本原理", "掌握Token识别方法"],
        "difficulty_level": "中级",
        "target_grade_level": "大学",
        "subject_area": "计算机科学",
        "procedural_concepts": [
            {
                "name": "词法分析过程",
                "description": "将源代码字符序列转换为Token序列的过程",
                "key_steps": [
                    "读取输入字符",
                    "使用正则表达式匹配Token模式",
                    "生成对应的Token",
                    "跳过空白字符",
                    "处理错误字符"
                ],
                "complexity": "中等"
            },
            {
                "name": "Token识别算法",
                "description": "基于正则表达式的Token识别和分类",
                "key_steps": [
                    "定义Token类型的正则表达式",
                    "按优先级匹配模式",
                    "返回最长匹配",
                    "生成Token对象"
                ],
                "complexity": "中等"
            }
        ]
    }

    # User preferences
    user_preferences = {
        "grade_level": "university",
        "interests": ["编程", "编译器"]
    }

    # Initialize Zhipu provider
    try:
        provider = ChineseProvider("40a114783556416892a6e3914856367f.xYQOslFt2fzVmER8")
        print("✅ Zhipu provider initialized successfully")

        # Test the modified generate_website function
        print("\n🔄 Testing modified website generation...")
        result = await provider.generate_website([], mock_analysis, user_preferences)

        if result:
            print("✅ Website generation successful!")
            print(f"📝 HTML length: {len(result.get('html', ''))}")
            print(f"📊 Metadata keys: {list(result.get('metadata', {}).keys())}")
            print(f"🎯 Interactive elements: {len(result.get('interactive_elements', []))}")

            # Save the result for inspection
            import datetime
            from pathlib import Path
            html_dir = Path("/Users/tsq/Documents/code/lear_your_way/backend/tests/html/")
            html_dir.mkdir(exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            html_filename = f"compiler_website_{timestamp}.html"
            html_filepath = html_dir / html_filename
            with open(html_filepath, 'w', encoding='utf-8') as f:
                f.write(result.get('html', ''))
            print("💾 HTML saved to ", html_filepath)

            # Print metadata
            metadata = result.get('metadata', {})
            print(f"\n📋 Metadata:")
            print(f"   Title: {metadata.get('title')}")
            print(f"   Subject: {metadata.get('subject')}")
            print(f"   Grade Level: {metadata.get('grade_level')}")
            print(f"   Estimated Time: {metadata.get('estimated_time_minutes')} minutes")

            # Print interactive elements
            elements = result.get('interactive_elements', [])
            print(f"\n🎮 Interactive Elements ({len(elements)}):")
            for i, element in enumerate(elements):
                print(f"   {i+1}. {element.get('type', 'unknown')}: {element.get('question', element.get('word', 'N/A'))}")

        else:
            print("❌ Website generation failed - no result returned")

    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Check if ZHIPU_API_KEY is set
    if not os.getenv("ZHIPU_API_KEY"):
        print("⚠️  Warning: ZHIPU_API_KEY not found in environment variables")
        print("   This test requires a valid Zhipu API key to work")
        print("   Set the environment variable and run again:")
        print("   export ZHIPU_API_KEY='your-api-key-here'")
        sys.exit(1)

    print("🚀 Testing modified GLM-4.6 website generation...")
    asyncio.run(test_modified_generation())