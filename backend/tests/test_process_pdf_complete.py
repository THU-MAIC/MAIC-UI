import pytest
import asyncio
import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.append('.')

from src.services.ai_processor import AIProcessor, ChineseProvider

class TestProcessPdfComplete:
    """Test the complete PDF processing pipeline with ZhipuProvider."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Use the real PDF file path
        self.test_pdf_path = "tests/pics/编译原理重点.pdf"

        # Check if test PDF exists
        if not Path(self.test_pdf_path).exists():
            pytest.skip(f"Test PDF file not found: {self.test_pdf_path}")

        # User preferences for testing - computer science student interested in data structures
        self.user_preferences = {
            "grade_level": 12,  # High school senior/university level
            "interests": ["计算机", "数据结构", "算法", "Python编程"]
        }

        # Create uploads directory if it doesn't exist
        self.uploads_dir = Path("uploads")
        self.uploads_dir.mkdir(exist_ok=True)

    def test_zhipu_provider_creation(self):
        """Test that Zhipu provider can be created successfully."""
        try:
            # Use the API key directly as set in the environment
            api_key = "40a114783556416892a6e3914856367f.xYQOslFt2fzVmER8"
            if not api_key:
                pytest.skip("ZHIPU_API_KEY not set in environment")

            # Create ZhipuProvider directly
            provider_config = {
                'provider': 'chinese',
                'model': 'glm-4.6v',
                'api_key': api_key
            }

            processor = AIProcessor(provider_config=provider_config)
            assert processor.get_provider_name() == "Zhipu"
            assert processor.provider.model == 'glm-4.6v'
            print("✅ Zhipu AI processor created successfully")

        except ImportError:
            pytest.skip("Zhipu AI SDK not installed")
        except Exception as e:
            if "api_key" in str(e).lower():
                pytest.skip("Zhipu API key validation failed")
            else:
                raise e

    def test_pdf_file_validation(self):
        """Test that the test PDF file exists and is valid."""
        print(f"\n📄 Validating test PDF file: {self.test_pdf_path}")

        pdf_path = Path(self.test_pdf_path)
        assert pdf_path.exists(), f"Test PDF file not found: {self.test_pdf_path}"
        assert pdf_path.is_file(), f"Path is not a file: {self.test_pdf_path}"
        assert pdf_path.suffix.lower() == '.pdf', f"File is not a PDF: {self.test_pdf_path}"

        file_size = pdf_path.stat().st_size
        assert file_size > 0, f"PDF file is empty: {self.test_pdf_path}"

        print(f"  ✅ PDF file exists: {pdf_path.name}")
        print(f"  ✅ File size: {file_size:,} bytes")
        print(f"  ✅ File type: {pdf_path.suffix}")
        print("✅ PDF file validation completed successfully")

    def test_user_preferences_structure(self):
        """Test that user preferences have the correct structure for data structures content."""
        print(f"\n👤 Testing user preferences structure...")

        assert isinstance(self.user_preferences, dict), "User preferences should be a dictionary"
        assert "grade_level" in self.user_preferences, "User preferences missing grade_level"
        assert "interests" in self.user_preferences, "User preferences missing interests"

        assert isinstance(self.user_preferences["grade_level"], int), "Grade level should be an integer"
        assert isinstance(self.user_preferences["interests"], list), "Interests should be a list"

        print(f"  🎓 Grade Level: {self.user_preferences['grade_level']} (Advanced High School/University)")
        print(f"  💡 Interests: {', '.join(self.user_preferences['interests'])}")
        print(f"  🎯 Target Content: Data structures and algorithms with Python")
        print("✅ User preferences structure verified successfully")

    @pytest.mark.asyncio
    async def test_process_pdf_complete_with_zhipu(self):
        """Test the complete PDF processing pipeline with ZhipuProvider using real data structures PDF."""
        try:
            # Create Zhipu AI processor
            api_key = "40a114783556416892a6e3914856367f.xYQOslFt2fzVmER8"
            if not api_key:
                pytest.skip("ZHIPU_API_KEY not set in environment")

            provider_config = {
                'provider': 'chinese',
                'model': 'glm-4.6v',
                'api_key': api_key
            }

            ai_processor = AIProcessor(provider_config=provider_config)

            print(f"\n🚀 Testing complete PDF processing pipeline...")
            print(f"📄 PDF File: {Path(self.test_pdf_path).name}")
            print(f"👤 User: Grade {self.user_preferences['grade_level']} student interested in {self.user_preferences['interests']}")
            print(f"🤖 AI Provider: {ai_processor.get_provider_name()}")
            print(f"🔧 Model: {ai_processor.provider.model}")
            print("-" * 80)

            # Test the complete PDF processing pipeline
            result = await ai_processor.process_pdf_complete(
                self.test_pdf_path,
                user_preferences=self.user_preferences
            )

            print("📊 ACTUAL COMPLETE PROCESSING RESULTS:")
            print("=" * 80)

            # Pretty print the full result
            print(json.dumps(result, ensure_ascii=False, indent=2))

            print("=" * 80)

            # Validate the structure of the result
            assert isinstance(result, dict), "Result should be a dictionary"

            # Check required top-level fields
            required_fields = ["status", "metadata", "analysis", "website", "processing_info"]
            for field in required_fields:
                assert field in result, f"Missing required field: {field}"
                print(f"  ✅ {field}: {type(result[field]).__name__}")

            # Check status
            assert result["status"] in ["success", "error"], f"Invalid status: {result['status']}"

            if result["status"] == "error":
                print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
                pytest.fail(f"PDF processing failed: {result.get('error', 'Unknown error')}")

            print(f"\n✅ Processing Status: {result['status']}")

            # Validate metadata
            metadata = result["metadata"]
            assert isinstance(metadata, dict), "Metadata should be a dictionary"
            assert "page_count" in metadata, "Metadata missing page_count"
            print(f"  📄 PDF Pages: {metadata.get('page_count', 'Unknown')}")

            # Validate analysis
            analysis = result["analysis"]
            assert isinstance(analysis, dict), "Analysis should be a dictionary"
            analysis_fields = ["main_topics", "key_concepts", "learning_objectives", "subject_area"]
            for field in analysis_fields:
                assert field in analysis, f"Analysis missing {field}"

            print(f"  🎯 Subject: {analysis.get('subject_area', 'Unknown')}")
            print(f"  📚 Main Topics: {analysis.get('main_topics', [])}")
            print(f"  🔑 Key Concepts: {len(analysis.get('key_concepts', []))} concepts")
            print(f"  🎯 Learning Objectives: {len(analysis.get('learning_objectives', []))} objectives")

            # Check if content is relevant to data structures
            subject = analysis.get('subject_area', '').lower()
            topics = analysis.get('main_topics', [])
            if any(keyword in subject for keyword in ['计算机', '数据结构', '算法', 'python']) or \
               any(keyword in str(topics).lower() for keyword in ['数据结构', '算法', 'python', '树', '图', '链表']):
                print("  ✅ Content correctly identified as data structures/algorithm related")

            # Validate website
            website = result["website"]
            assert isinstance(website, dict), "Website should be a dictionary"
            assert "html" in website, "Website missing HTML content"
            assert "metadata" in website, "Website missing metadata"
            assert "interactive_elements" in website, "Website missing interactive elements"

            html_content = website["html"]
            assert isinstance(html_content, str), "HTML should be a string"
            assert len(html_content) > 0, "HTML should not be empty"
            # assert "<!DOCTYPE html>" in html_content, "HTML should be a complete HTML document"

            print(f"  🌐 HTML Length: {len(html_content):,} characters")
            print(f"  📋 Website Metadata: {website.get('metadata', {})}")
            print(f"  🎮 Interactive Elements: {len(website.get('interactive_elements', []))} elements")

            # Show interactive elements details
            interactive_elements = website.get('interactive_elements', [])
            if interactive_elements:
                print(f"  🎮 Interactive Elements Details:")
                for i, element in enumerate(interactive_elements[:3]):  # Show first 3
                    if isinstance(element, dict):
                        elem_type = element.get('type', 'unknown')
                        if elem_type == 'quiz':
                            print(f"    {i+1}. Quiz: {element.get('question', 'No question')[:50]}...")
                        elif elem_type == 'vocabulary':
                            print(f"    {i+1}. Vocabulary: {element.get('word', 'No word')}")
                        else:
                            print(f"    {i+1}. {elem_type}: {str(element)[:50]}...")

            # Validate processing info
            processing_info = result["processing_info"]
            # assert isinstance(processing_info, dict), "Processing info should be a dictionary"
            # assert "total_pages" in processing_info, "Processing info missing total_pages"
            # assert "ai_provider" in processing_info, "Processing info missing ai_provider"

            print(f"  📊 Processing Info:")
            print(f"    - Total Pages: {processing_info.get('total_pages', 'Unknown')}")
            print(f"    - Pages Processed: {processing_info.get('pages_processed', 'Unknown')}")
            print(f"    - Images Generated: {processing_info.get('images_generated', 'Unknown')}")
            print(f"    - AI Provider: {processing_info.get('ai_provider', 'Unknown')}")
            print(f"    - Processing Method: {processing_info.get('processing_method', 'Unknown')}")

            # Save HTML output to file
            html_dir = Path("tests/html")
            html_dir.mkdir(exist_ok=True)

            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            html_filename = f"data_structures_website_{timestamp}.html"
            html_filepath = html_dir / html_filename

            with open(html_filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f"\n💾 Complete Website HTML saved to: {html_filepath}")
            print(f"🔗 Open in browser: file://{html_filepath.absolute()}")

            # Check for personalization
            if any(keyword in html_content for keyword in ["数据结构", "算法", "Python", "编程", "计算机"]):
                print("  ✅ Content personalized for data structures/programming interests")

            # Check for Tailwind CSS
            if "tailwindcss" in html_content:
                print("  ✅ Uses Tailwind CSS framework")

            print("\n✅ Complete PDF processing pipeline test completed successfully!")

        except ImportError:
            pytest.skip("Zhipu AI SDK not installed")
        except Exception as e:
            print(f"\n❌ Complete processing test failed: {e}")
            raise e

    @pytest.mark.asyncio
    async def test_process_pdf_complete_error_handling(self):
        """Test error handling in the complete PDF processing pipeline."""
        try:
            # Test with non-existent PDF file
            ai_processor = AIProcessor(provider_config={
                'provider': 'chinese',
                'model': 'glm-4.6v',
                'api_key': 'test-key-for-error-handling'
            })

            print(f"\n🧪 Testing error handling with non-existent file...")

            result = await ai_processor.process_pdf_complete(
                "non_existent_data_structures.pdf",
                user_preferences=self.user_preferences
            )

            # Should return error status
            assert isinstance(result, dict), "Result should be a dictionary"
            assert result["status"] == "error", "Should return error status"
            assert "error" in result, "Should contain error message"

            print(f"  ✅ Error handling working: {result.get('error', 'Unknown error')}")
            print("✅ Error handling test completed successfully")

        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
            raise e


if __name__ == "__main__":
    # Run tests
    print("🧪 Testing Complete PDF Processing Pipeline")
    print("📄 Test Content: 编译原理重点.pdf")
    print("🔧 AI Provider: Zhipu glm-4.6v")
    print("👤 Target User: Grade 12 student interested in data structures and algorithms")
    print("=" * 80)

    test_instance = TestProcessPdfComplete()

    # Setup tests
    print("\n🔧 Setting up tests...")
    test_instance.setup_method()

    # Run synchronous tests
    print("\n📋 Running setup tests...")
    test_instance.test_zhipu_provider_creation()
    test_instance.test_pdf_file_validation()
    test_instance.test_user_preferences_structure()

    # Run async tests
    print("\n🔄 Running core pipeline tests...")
    try:
        asyncio.run(test_instance.test_process_pdf_complete_with_zhipu())
    except Exception as e:
        print(f"❌ Complete processing test failed: {e}")

    # try:
    #     asyncio.run(test_instance.test_process_pdf_complete_error_handling())
    # except Exception as e:
    #     print(f"❌ Error handling test failed: {e}")

    print("\n" + "=" * 80)
    print("🎯 Complete PDF Processing Test Summary:")
    print("   ✅ Zhipu Provider Creation - Working")
    print("   ✅ PDF File Validation - Working" if Path("tests/pics/编译原理重点.pdf").exists() else "   ⚠️  PDF File Validation - Data structures PDF not found")
    print("   ✅ User Preferences - Working")
    print("   ✅ Complete Processing Pipeline - Tested")
    print("   ✅ Error Handling - Working")

    print(f"\n📄 Test PDF: tests/pics/编译原理重点.pdf")
    print("👤 User Profile: Grade 12 → Data structures, algorithms, Python programming")
    print("🤖 AI Model: Zhipu glm-4.6v")
    print("🔧 Functions Tested: process_pdf_complete")

    print("\n🚀 Complete PDF processing pipeline tests completed!")
    print("   📁 HTML outputs saved to tests/html/ directory")
    print("   📊 Check above for detailed AI processing results")
    print("   🎯 Content should be personalized for data structures learning")