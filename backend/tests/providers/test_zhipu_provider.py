import pytest
import asyncio
import sys
import os
import base64
import json
from pathlib import Path

# Add project root to path
sys.path.append('.')

from src.services.ai_processor import AIProcessor, ChineseProvider

class TestChineseProvider:
    """Test the Zhipu AI provider integration - focusing on analyze_content and generate_website functions."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Load test images
        self.test_images = []

        # Path to test images
        image_1_path = Path("tests/pics/1.png")
        image_2_path = Path("tests/pics/2.png")

        # Load images if they exist
        if image_1_path.exists():
            with open(image_1_path, "rb") as img_file:
                img_data = base64.b64encode(img_file.read()).decode()
                self.test_images.append({
                    "page": 1,
                    "image_data": img_data,
                    "format": "PNG",
                    "width": 800,
                    "height": 600
                })

        if image_2_path.exists():
            with open(image_2_path, "rb") as img_file:
                img_data = base64.b64encode(img_file.read()).decode()
                self.test_images.append({
                    "page": 2,
                    "image_data": img_data,
                    "format": "PNG",
                    "width": 800,
                    "height": 600
                })

        # User preferences for testing - young student interested in computer science
        self.user_preferences = {
            "grade_level": 10,  # High school student
            "interests": ["计算机", "人工智能", "技术", "编程"]
        }

    def test_provider_creation(self):
        """Test that Zhipu provider can be created successfully."""
        try:
            # Use API key from environment
            api_key = "40a114783556416892a6e3914856367f.xYQOslFt2fzVmER8"
            if not api_key:
                pytest.skip("ZHIPU_API_KEY not set in environment")

            provider = ChineseProvider(api_key=api_key)
            assert provider.get_provider_name() == "Zhipu"
            assert provider.model == "glm-4.6v"
            print("✅ Zhipu provider created successfully")

        except ImportError:
            pytest.skip("Zhipu AI SDK not installed")
        except Exception as e:
            if "api_key" in str(e).lower():
                pytest.skip("Zhipu API key validation failed")
            else:
                raise e

    @pytest.mark.asyncio
    async def test_analyze_content_with_real_images(self):
        """Test analyze_content function with real Qwen3-VL tech report images and show the actual output."""
        if not self.test_images:
            pytest.skip("Test images not found in tests/pics/")

        try:
            # Try to create provider with environment API key
            api_key = "40a114783556416892a6e3914856367f.xYQOslFt2fzVmER8"
            if not api_key:
                pytest.skip("ZHIPU_API_KEY not set in environment")

            provider = ChineseProvider(api_key=api_key)

            print(f"\n🧠 Testing content analysis with {len(self.test_images)} Qwen3-VL tech report images...")
            print(f"👤 User Profile: Grade {self.user_preferences['grade_level']} student interested in {self.user_preferences['interests']}")
            print(f"🔧 Using Zhipu GLM-4.5v model with thinking mode enabled")
            print("-" * 60)

            # Test the analyze_content function
            analysis = await provider.analyze_content(self.test_images, self.user_preferences)

            print("📊 ACTUAL AI ANALYSIS RESULTS:")
            print("=" * 60)

            # Pretty print the full analysis
            print(json.dumps(analysis, ensure_ascii=False, indent=2))

            print("=" * 60)
            print("\n📋 Analysis Breakdown:")

            # Verify the structure and show key insights
            assert isinstance(analysis, dict), "Analysis should return a dictionary"

            # Check required fields and show their content
            required_fields = [
                "main_topics", "key_concepts", "learning_objectives",
                "difficulty_level", "target_grade_level", "content_structure",
                "visual_elements", "subject_area"
            ]

            for field in required_fields:
                assert field in analysis, f"Missing required field: {field}"
                content = analysis[field]
                if isinstance(content, list):
                    print(f"  📌 {field}: {content}")
                else:
                    print(f"  📌 {field}: {content}")

            # Analysis validation
            assert isinstance(analysis["main_topics"], list), "main_topics should be a list"
            assert isinstance(analysis["key_concepts"], list), "key_concepts should be a list"
            assert isinstance(analysis["learning_objectives"], list), "learning_objectives should be a list"
            assert isinstance(analysis["difficulty_level"], str), "difficulty_level should be a string"
            assert isinstance(analysis["subject_area"], str), "subject_area should be a string"

            # Check if content is real or fallback
            if analysis["main_topics"] == ["教育内容"]:
                print("\n⚠️  AI used fallback content (API call may have failed)")
            else:
                print(f"\n✅ Real AI analysis generated!")
                print(f"🎯 Identified Subject: {analysis['subject_area']}")
                print(f"📚 Main Topics: {analysis['main_topics']}")
                print(f"🔑 Key Concepts: {len(analysis['key_concepts'])} concepts identified")
                print(f"🎯 Learning Objectives: {len(analysis['learning_objectives'])} objectives set")
                print(f"📈 Difficulty Level: {analysis['difficulty_level']}")
                print(f"👥 Target Grade: {analysis['target_grade_level']}")

            print("\n✅ analyze_content function test completed successfully")

        except ImportError:
            pytest.skip("Zhipu AI SDK not installed")
        except Exception as e:
            print(f"\n❌ analyze_content test failed: {e}")
            raise e

    @pytest.mark.asyncio
    async def test_generate_website_with_real_images(self):
        """Test generate_website function with real Qwen3-VL tech report images and show the actual HTML output."""
        if not self.test_images:
            pytest.skip("Test images not found in tests/pics/")

        try:
            # Try to create provider with environment API key
            api_key = "40a114783556416892a6e3914856367f.xYQOslFt2fzVmER8"
            if not api_key:
                pytest.skip("ZHIPU_API_KEY not set in environment")

            provider = ChineseProvider(api_key=api_key)

            print(f"\n🌐 Testing website generation with {len(self.test_images)} Qwen3-VL tech report images...")
            print(f"👤 User Profile: Grade {self.user_preferences['grade_level']} student interested in {self.user_preferences['interests']}")
            print(f"🔧 Using Zhipu GLM-4.5v model with thinking mode enabled")
            print("-" * 60)

            # First get content analysis
            analysis = await provider.analyze_content(self.test_images, self.user_preferences)

            print("📊 Using this analysis for website generation:")
            print(f"  Subject: {analysis.get('subject_area', 'Unknown')}")
            print(f"  Topics: {analysis.get('main_topics', [])}")
            print(f"  Difficulty: {analysis.get('difficulty_level', 'Unknown')}")
            print("-" * 60)

            # Test the generate_website function
            website_result = await provider.generate_website(self.test_images, analysis, self.user_preferences)

            print("🌐 ACTUAL AI-GENERATED WEBSITE:")
            print("=" * 60)

            # Verify the structure
            assert isinstance(website_result, dict), "Website result should return a dictionary"

            # Check required fields
            required_fields = ["html", "metadata", "interactive_elements"]
            for field in required_fields:
                assert field in website_result, f"Missing required field: {field}"

            # Show metadata
            metadata = website_result["metadata"]
            print("📋 Website Metadata:")
            for key, value in metadata.items():
                print(f"  📌 {key}: {value}")

            # Show interactive elements
            interactive_elements = website_result["interactive_elements"]
            print(f"\n🎮 Interactive Elements ({len(interactive_elements)} found):")
            for i, element in enumerate(interactive_elements[:5]):  # Show first 5 elements
                print(f"  {i+1}. {json.dumps(element, ensure_ascii=False, indent=4)}")

            # Get HTML content
            html_content = website_result["html"]

            # Create html directory if it doesn't exist
            html_dir = Path("tests/html")
            html_dir.mkdir(exist_ok=True)

            # Generate filename with timestamp
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            html_filename = f"qwen3vl_website_{timestamp}.html"
            html_filepath = html_dir / html_filename

            # Save HTML file
            with open(html_filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f"\n📄 Generated HTML Content (Length: {len(html_content)} characters):")
            print(f"💾 Saved to: {html_filepath}")
            print("=" * 60)
            print(f"📂 File: {html_filename}")
            print(f"🔗 Open in browser: file://{html_filepath.absolute()}")
            print("=" * 60)

            # HTML validation
            assert isinstance(html_content, str), "HTML should be a string"
            assert len(html_content) > 0, "HTML should not be empty"
            assert "<!DOCTYPE html>" in html_content, "HTML should be a complete HTML document"
            assert "<html" in html_content, "HTML should contain html tag"

            # Show features analysis
            print("\n🔍 Website Features Analysis:")

            # Check for personalization
            if any(keyword in html_content for keyword in ["计算机", "人工智能", "编程", "技术"]):
                print("  ✅ Content personalized for computer science interests")
            else:
                print("  ⚠️  Limited personalization detected")

            # Check for Tailwind CSS
            if "tailwindcss" in html_content:
                print("  ✅ Uses Tailwind CSS framework")
            else:
                print("  ⚠️  Tailwind CSS not detected")

            # Check for interactive features
            if "quiz" in html_content.lower() or "button" in html_content.lower():
                print("  ✅ Contains interactive elements")
            else:
                print("  ⚠️  Limited interactivity detected")

            # Check for age-appropriate content
            if str(self.user_preferences['grade_level']) in html_content:
                print("  ✅ Content mentions grade level appropriateness")

            print(f"\n📊 Interactive Elements Summary:")
            print(f"  📝 Total elements: {len(interactive_elements)}")
            element_types = {}
            for element in interactive_elements:
                if isinstance(element, dict) and "type" in element:
                    element_types[element["type"]] = element_types.get(element["type"], 0) + 1
            for elem_type, count in element_types.items():
                print(f"  📌 {elem_type}: {count}")

            print("\n✅ generate_website function test completed successfully")

        except ImportError:
            pytest.skip("Zhipu AI SDK not installed")
        except Exception as e:
            print(f"\n❌ generate_website test failed: {e}")
            raise e

    def test_image_loading(self):
        """Test that Qwen3-VL tech report images are loaded correctly."""
        print("\n🖼️  Testing Qwen3-VL tech report image loading...")
        print("-" * 40)

        if not self.test_images:
            pytest.skip("Test images not found in tests/pics/")

        print(f"📊 Loaded {len(self.test_images)} Qwen3-VL tech report images:")

        for i, img in enumerate(self.test_images):
            # Verify structure
            assert "page" in img, f"Image {i+1} missing page number"
            assert "image_data" in img, f"Image {i+1} missing image_data"
            assert "format" in img, f"Image {i+1} missing format"
            assert img["page"] == i + 1, f"Image {i+1} has incorrect page number"

            # Verify base64 data
            assert len(img["image_data"]) > 0, f"Image {i+1} has empty image_data"

            try:
                decoded = base64.b64decode(img["image_data"])
                assert len(decoded) > 0, f"Image {i+1} base64 data is invalid"
                print(f"  ✅ Page {img['page']}: {img['format']}, {len(decoded)} bytes, {len(img['image_data'])} chars base64")
            except Exception as e:
                pytest.fail(f"Image {i+1} has invalid base64 data: {e}")

        print("✅ Qwen3-VL tech report image loading completed successfully")

    def test_user_preferences_structure(self):
        """Test that user preferences have correct structure for computer science student."""
        print("\n👤 Testing computer science student preferences...")
        print("-" * 40)

        assert isinstance(self.user_preferences, dict), "User preferences should be a dictionary"
        assert "grade_level" in self.user_preferences, "User preferences missing grade_level"
        assert "interests" in self.user_preferences, "User preferences missing interests"

        assert isinstance(self.user_preferences["grade_level"], int), "Grade level should be an integer"
        assert isinstance(self.user_preferences["interests"], list), "Interests should be a list"

        print(f"  🎓 Grade Level: {self.user_preferences['grade_level']} (High School)")
        print(f"  💡 Interests: {', '.join(self.user_preferences['interests'])}")
        print(f"  🎯 Target Content: Computer science and AI focused")
        print("✅ Computer science student preferences verified successfully")


if __name__ == "__main__":
    # Run tests
    print("🧪 Testing Zhipu AI Provider - analyze_content & generate_website")
    print("📋 Test Content: Qwen3-VL Tech Report Pages")
    print("👤 Target User: Grade 10 student interested in computer science")
    print("🔧 AI Model: Zhipu GLM-4.5v with thinking mode")
    print("=" * 80)

    test_instance = TestChineseProvider()

    # Setup tests
    print("\n🔧 Setting up tests...")
    test_instance.setup_method()

    # Run synchronous tests
    print("\n📋 Running setup tests...")
    test_instance.test_image_loading()
    test_instance.test_user_preferences_structure()

    # Provider tests
    print("\n🤖 Running provider tests...")
    try:
        test_instance.test_provider_creation()
    except Exception as e:
        print(f"❌ Provider creation failed: {e}")

    # Run async tests
    print("\n🔄 Running core function tests...")
    try:
        asyncio.run(test_instance.test_analyze_content_with_real_images())
    except Exception as e:
        print(f"❌ Content analysis test failed: {e}")

    try:
        asyncio.run(test_instance.test_generate_website_with_real_images())
    except Exception as e:
        print(f"❌ Website generation test failed: {e}")

    print("\n" + "=" * 80)
    print("🎯 Test Summary:")
    print(f"📊 Test Images: {len(test_instance.test_images)} Qwen3-VL tech report pages")
    print("👤 User Profile: Grade 10 student → Computer science interests")
    print("🧠 Functions Tested: analyze_content, generate_website")
    print("🔑 API Key: ZHIPU_API_KEY environment variable")
    print("🤖 AI Model: GLM-4.5v with thinking mode enabled")

    print("\n🚀 All tests completed! Check above for detailed AI outputs.")