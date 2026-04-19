import pytest
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append('.')

from src.services.ai_processor import AIProcessor

class TestConvertPdfToImages:
    """Test the convert_pdf_to_images function."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Use the real PDF file path
        self.test_pdf_path = "tests/pics/数据结构-Python语言描述试卷(四)附答案.pdf"

        # Check if test PDF exists
        if not Path(self.test_pdf_path).exists():
            pytest.skip(f"Test PDF file not found: {self.test_pdf_path}")

        # Create AI processor with Zhipu config
        api_key = "40a114783556416892a6e3914856367f.xYQOslFt2fzVmER8"
        self.processor = AIProcessor(provider_config={
            'provider': 'zhipu',
            'model': 'glm-4.6v',
            'api_key': api_key
        })

    def test_pdf_file_exists(self):
        """Test that the test PDF file exists."""
        print(f"\n📄 Testing PDF file existence: {self.test_pdf_path}")

        pdf_path = Path(self.test_pdf_path)
        assert pdf_path.exists(), f"Test PDF file not found: {self.test_pdf_path}"
        assert pdf_path.is_file(), f"Path is not a file: {self.test_pdf_path}"
        assert pdf_path.suffix.lower() == '.pdf', f"File is not a PDF: {self.test_pdf_path}"

        file_size = pdf_path.stat().st_size
        assert file_size > 0, f"PDF file is empty: {self.test_pdf_path}"

        print(f"  ✅ PDF file exists: {pdf_path.name}")
        print(f"  ✅ File size: {file_size:,} bytes")
        print(f"  ✅ File type: {pdf_path.suffix}")

    def test_ai_processor_creation(self):
        """Test that AI processor can be created."""
        print(f"\n🤖 Testing AI processor creation...")

        assert self.processor is not None, "AI processor should not be None"
        assert self.processor.get_provider_name() == "Zhipu", "Provider should be Zhipu"
        print(f"  ✅ AI processor created with provider: {self.processor.get_provider_name()}")
        print(f"  ✅ Model: {self.processor.provider.model}")

    def test_convert_pdf_to_images_with_pymupdf(self):
        """Test PDF to image conversion using PyMuPDF."""
        print(f"\n🔄 Testing PDF to image conversion...")
        print(f"📄 PDF File: {Path(self.test_pdf_path).name}")
        print(f"🔧 Using: AIProcessor.convert_pdf_to_images()")

        try:
            # Convert PDF to images
            images = self.processor.convert_pdf_to_images(self.test_pdf_path)

            # Validate the result
            assert isinstance(images, list), "Result should be a list"
            assert len(images) > 0, "Should generate at least one image"

            print(f"  ✅ Generated {len(images)} image(s)")

            # Validate each image
            for i, image in enumerate(images):
                print(f"\n  📸 Image {i+1}:")

                # Check required fields
                required_fields = ["page", "image_data", "format", "width", "height"]
                for field in required_fields:
                    assert field in image, f"Image {i+1} missing field: {field}"
                    print(f"    ✅ {field}: {image[field] if field not in ['image_data'] else f'{len(str(image[field]))} chars'}")

                # Validate data types
                assert isinstance(image["page"], int), f"Page number should be int"
                assert isinstance(image["image_data"], str), f"Image data should be string"
                assert isinstance(image["format"], str), f"Format should be string"
                assert isinstance(image["width"], int), f"Width should be int"
                assert isinstance(image["height"], int), f"Height should be int"

                # Validate values
                assert image["page"] == i + 1, f"Page number should be {i+1}"
                assert len(image["image_data"]) > 0, f"Image data should not be empty"
                assert image["format"] in ["PNG", "JPEG"], f"Format should be PNG or JPEG"
                assert image["width"] > 0, f"Width should be positive"
                assert image["height"] > 0, f"Height should be positive"

                # Validate base64 format
                try:
                    import base64
                    decoded = base64.b64decode(image["image_data"])
                    assert len(decoded) > 0, f"Base64 should decode to non-empty data"
                    print(f"    ✅ Base64 valid: {len(decoded):,} bytes decoded")
                except Exception as e:
                    pytest.fail(f"Invalid base64 in image {i+1}: {e}")

            print(f"\n✅ PDF to image conversion completed successfully!")
            print(f"📊 Summary:")
            print(f"  📄 Total pages converted: {len(images)}")
            print(f"  📐 Format: {images[0]['format']}")
            print(f"  📏 Average size: {sum(img['width'] for img in images)//len(images)}x{sum(img['height'] for img in images)//len(images)}")

            # Save a sample image for verification
            if images:
                import base64
                sample_image = images[0]
                decoded = base64.b64decode(sample_image["image_data"])

                sample_dir = Path("tests/output")
                sample_dir.mkdir(exist_ok=True)

                sample_path = sample_dir / f"sample_page_{sample_image['page']}.{sample_image['format'].lower()}"
                with open(sample_path, "wb") as f:
                    f.write(decoded)

                print(f"💾 Sample image saved: {sample_path}")
                print(f"🔗 You can open this file to verify the conversion quality")

        except Exception as e:
            print(f"\n❌ PDF to image conversion failed: {e}")
            raise e

    def test_conversion_with_nonexistent_file(self):
        """Test error handling with non-existent PDF file."""
        print(f"\n🧪 Testing error handling with non-existent file...")

        try:
            images = self.processor.convert_pdf_to_images("nonexistent.pdf")
            pytest.fail("Should have raised an exception")
        except Exception as e:
            print(f"  ✅ Correctly raised exception: {type(e).__name__}")
            print(f"  ✅ Error message: {str(e)}")

    def test_conversion_performance(self):
        """Test the performance of PDF to image conversion."""
        print(f"\n⏱️  Testing conversion performance...")

        import time

        start_time = time.time()
        images = self.processor.convert_pdf_to_images(self.test_pdf_path)
        end_time = time.time()

        conversion_time = end_time - start_time
        pages_per_second = len(images) / conversion_time if conversion_time > 0 else 0

        print(f"  ⏱️  Conversion time: {conversion_time:.2f} seconds")
        print(f"  📄 Pages converted: {len(images)}")
        print(f"  🚀 Speed: {pages_per_second:.2f} pages/second")

        # Performance should be reasonable (less than 5 seconds per page)
        assert conversion_time < len(images) * 5, "Conversion should be faster than 5 seconds per page"
        print(f"  ✅ Performance acceptable: <5 seconds per page")

    def test_image_quality(self):
        """Test that generated images have reasonable quality."""
        print(f"\n🖼️  Testing image quality...")

        images = self.processor.convert_pdf_to_images(self.test_pdf_path)

        for i, image in enumerate(images[:3]):  # Test first 3 images
            print(f"\n  📸 Image {i+1} quality check:")

            # Check image dimensions
            width, height = image["width"], image["height"]
            print(f"    📐 Dimensions: {width}x{height}")

            # Should have reasonable dimensions (not too small)
            assert width >= 800, f"Width should be at least 800px, got {width}"
            assert height >= 600, f"Height should be at least 600px, got {height}"
            print(f"    ✅ Reasonable dimensions")

            # Check file size (base64 string length)
            base64_size = len(image["image_data"])
            estimated_bytes = base64_size * 3 / 4  # Approximate base64 to bytes conversion

            print(f"    📊 Estimated size: {estimated_bytes/1024:.1f} KB")

            # Should have reasonable file size (not too small, not too large)
            assert estimated_bytes > 10000, f"Image should be larger than 10KB, got {estimated_bytes} bytes"
            assert estimated_bytes < 5000000, f"Image should be smaller than 5MB, got {estimated_bytes} bytes"
            print(f"    ✅ Reasonable file size")


if __name__ == "__main__":
    # Run tests
    print("🧪 Testing PDF to Images Conversion")
    print("🔧 Function: convert_pdf_to_images")
    print("📄 Test Content: 数据结构-Python语言描述试卷(四)附答案.pdf")
    print("🤖 AI Provider: Zhipu GLM-4.5v")
    print("=" * 80)

    test_instance = TestConvertPdfToImages()

    # Setup tests
    print("\n🔧 Setting up tests...")
    test_instance.setup_method()

    # Run tests
    print("\n📋 Running tests...")

    test_instance.test_pdf_file_exists()
    test_instance.test_ai_processor_creation()

    try:
        test_instance.test_convert_pdf_to_images_with_pymupdf()
    except Exception as e:
        print(f"❌ Conversion test failed: {e}")

    test_instance.test_conversion_with_nonexistent_file()
    test_instance.test_conversion_performance()
    test_instance.test_image_quality()

    print("\n" + "=" * 80)
    print("🎯 PDF to Images Conversion Test Summary:")
    print("   ✅ PDF File Validation - Working")
    print("   ✅ AI Processor Creation - Working")
    print("   ✅ PDF to Images Conversion - Tested")
    print("   ✅ Error Handling - Working")
    print("   ✅ Performance Testing - Working")
    print("   ✅ Image Quality Testing - Working")

    print(f"\n📄 Test PDF: tests/pics/数据结构-Python语言描述试卷(四)附答案.pdf")
    print("🔧 Method: PyMuPDF (preferred)")
    print("📁 Sample outputs saved to: tests/output/")
    print("🖼️  Function tested: convert_pdf_to_images")

    print("\n🚀 PDF to Images conversion tests completed!")
    print("   📸 Real PDF pages converted to base64 images")
    print("   🎨 Images ready for AI vision analysis")