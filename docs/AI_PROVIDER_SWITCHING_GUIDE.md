# AI Provider Switching Guide

## 🎯 Overview

The Learn Your Way PDF processing system now supports multiple AI providers through a clean, abstracted interface. You can easily switch between **Google Gemini** and **OpenAI GPT-4 Vision** without changing any code - just configuration!

---

## 🚀 **How to Switch AI Providers**

### **Method 1: Environment Variables (Recommended)**

Edit your `.env` file in `/backend/`:

```bash
# For Unified English Provider (Recommended - works in China)
AI_PROVIDER=english
ENGLISH_API_KEY=your_middle_transfer_api_key_here
ENGLISH_MODEL=gpt-4.1

# For specific models through English provider:
AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3-pro-image-preview

AI_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4.1

# For Chinese AI (Zhipu)
AI_PROVIDER=zhipu
ZHIPU_API_KEY=your_zhipu_api_key_here
ZHIPU_MODEL=glm-4.5v
```

### **Method 2: Programmatic Configuration**

```python
from src.services.ai_processor import AIProcessor

# Use Unified English Provider (recommended)
english_config = {
    'provider': 'english',
    'api_key': 'your_middle_transfer_key',
    'model': 'gpt-4.1'
}
processor = AIProcessor(provider_config=english_config)

# Use Gemini through English provider
gemini_config = {
    'provider': 'gemini',
    'api_key': 'your_middle_transfer_key',
    'model': 'gemini-3-pro-image-preview'
}
processor = AIProcessor(provider_config=gemini_config)

# Use OpenAI through English provider
openai_config = {
    'provider': 'openai',
    'api_key': 'your_middle_transfer_key',
    'model': 'gpt-4.1'
}
processor = AIProcessor(provider_config=openai_config)

# Use Chinese AI
zhipu_config = {
    'provider': 'zhipu',
    'api_key': 'your_zhipu_key',
    'model': 'glm-4.5v'
}
processor = AIProcessor(provider_config=zhipu_config)
```

---

## 🔄 **Live Switching Example**

```python
# Start with Gemini
processor = AIProcessor(provider_config={'provider': 'gemini', 'api_key': 'gemini_key'})
print(f"Current provider: {processor.get_provider_name()}")  # "Gemini"

# Switch to OpenAI - No code changes needed!
processor = AIProcessor(provider_config={'provider': 'openai', 'api_key': 'openai_key'})
print(f"Current provider: {processor.get_provider_name()}")  # "OpenAI"
```

---

## 📊 **Supported AI Providers**

| Provider | Vision Model | Text Model | Language Support | Status |
|----------|-------------|------------|----------------|--------|
| **English (Unified)** | `gemini-3-pro-image-preview`, `gpt-4.1` | Multiple models | **English** | ✅ **NEW Unified** |
| **Zhipu AI** | `glm-4.5v` | `glm-4.5v` | **Chinese 优化** | ✅ **Integrated** |

### **🚀 English Provider - Unified Access**
The English provider combines Gemini and OpenAI access through a single Chinese middle-transfer API:

**Models Supported:**
- **Gemini**: `gemini-3-pro-image-preview`, `gemini-pro-vision`
- **OpenAI**: `gpt-4.1`, `gpt-4-vision-preview`
- **Base URL**: `https://chatapi.onechats.ai/v1beta`

**Advantages:**
- ✅ **Single API Key** for both Gemini and OpenAI
- ✅ **Chinese Optimized** - works from mainland China
- ✅ **Model Switching** without code changes
- ✅ **Unified Interface** - same API format for all models
- ✅ **Fallback Support** - robust error handling

---

## 🛠 **Code Architecture Benefits**

### **Before (Tightly Coupled):**
```python
# OLD - Hardcoded to Gemini
from src.services.gemini_processor import GeminiPDFProcessor

processor = GeminiPDFProcessor()
result = processor.process_pdf_complete(pdf_path, user_prefs)
```

### **After (Abstracted & Flexible):**
```python
# NEW - Provider Agnostic
from src.services.ai_processor import AIProcessor

# Works with ANY configured provider!
processor = AIProcessor()
result = await processor.process_pdf_complete(pdf_path, user_prefs)
```

---

## 🔧 **Adding New AI Providers**

The abstraction makes it easy to add new providers:

```python
class ClaudeProvider(AIProvider):
    """Anthropic Claude provider implementation."""

    def __init__(self, api_key: str, model: str = "claude-3-opus"):
        # Initialize Claude client
        pass

    async def analyze_content(self, images, user_prefs):
        # Claude-specific implementation
        pass

    async def generate_website(self, images, analysis, user_prefs):
        # Claude-specific implementation
        pass

    def get_provider_name(self):
        return "Claude"

# Add to AIProcessor._create_provider_from_config()
elif provider_type == 'claude':
    return ClaudeProvider(api_key=config.get('api_key'))
```

---

## 🎛 **Configuration Options**

### **Environment Variables:**
- `AI_PROVIDER`: `gemini` or `openai`
- `GEMINI_API_KEY`: Your Google Gemini API key
- `OPENAI_API_KEY`: Your OpenAI API key
- `OPENAI_MODEL`: OpenAI model (default: `gpt-4-vision-preview`)

### **Provider Config Dictionary:**
```python
config = {
    'provider': 'openai',           # Required
    'api_key': 'sk-...',           # Required
    'model': 'gpt-4-vision-preview' # Optional (provider-specific)
}
```

---

## ✅ **Benefits of the Abstraction**

1. **🔄 Zero Code Changes**: Switch providers by changing config only
2. **🧪 Easy Testing**: Mock providers for unit tests
3. **📈 Future-Proof**: Add new providers without touching business logic
4. **🛡️ Consistent Interface**: Same API across all providers
5. **🎛 Flexible Configuration**: Environment + programmatic options
6. **⚡ Performance**: Provider-specific optimizations
7. **🌍 China Optimized**: English provider works through Chinese middle-transfer API
8. **🔗 Unified Access**: Single API key for both Gemini and OpenAI models
9. **🚀 Model Flexibility**: Easy switching between AI models without code changes

---

## 🚀 **Quick Start Examples**

### **Switch to Gemini:**
```bash
# .env
AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_key
```

### **Switch to OpenAI:**
```bash
# .env
AI_PROVIDER=openai
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4-vision-preview
```

### **Check Current Provider:**
```python
from src.services.ai_processor import AIProcessor
processor = AIProcessor()
info = processor.get_provider_info()
print(f"Provider: {info['provider']}")
print(f"Available: {info['available_providers']}")
```

---

## 🎯 **Real-World Usage**

```python
# API endpoint uses abstracted processor
@router.post("/api/pdf/upload")
async def upload_pdf(file: UploadFile, ...):
    # Gets configured provider automatically!
    ai_processor = get_ai_processor()

    # Same interface for Gemini OR OpenAI
    result = await ai_processor.process_pdf_complete(
        file_path,
        user_preferences
    )

    # Result format is identical regardless of provider
    return {
        "status": result["status"],
        "website": result["website"]["html"],
        "analysis": result["analysis"],
        "ai_provider": result["processing_info"]["ai_provider"]
    }
```

---

## 🔍 **Migration from Old System**

**Old System:**
```python
# Tied to specific AI provider
from src.services.gemini_processor import GeminiPDFProcessor
processor = GeminiPDFProcessor()
```

**New System:**
```python
# Provider-agnostic
from src.services.ai_processor import AIProcessor
processor = AIProcessor()  # Uses env config by default
```

**Migration Steps:**
1. ✅ Update imports: `gemini_processor` → `ai_processor`
2. ✅ Update instantiation: `GeminiPDFProcessor()` → `AIProcessor()`
3. ✅ Add async/await where needed
4. ✅ Configure provider in `.env`
5. ✅ Test with your preferred provider

---

## 🎉 **You're All Set!**

Your PDF processing system is now:
- ✅ **Provider Agnostic** - Easy to switch AI models
- ✅ **Future Ready** - Add new providers effortlessly
- ✅ **Backwards Compatible** - Same functionality as before
- ✅ **Testable** - Mock providers for development
- ✅ **Configurable** - Environment + programmatic control

**Just change `AI_PROVIDER=english`, `AI_PROVIDER=gemini`, `AI_PROVIDER=openai`, or `AI_PROVIDER=zhipu` in your `.env` file and you're good to go! 🚀**

---

## 🧪 **Testing & Verification**

All AI providers have been thoroughly tested with comprehensive test suites:

### **Zhipu AI Testing Results:**
```bash
🧪 Testing Zhipu AI Provider Integration
==================================================
✅ Provider creation - Working
✅ Custom model support - Working
✅ API key validation - Working
✅ Fallback functionality - Working
✅ Chinese prompts - Working
✅ Content structure - Working
✅ Environment configuration - Working
✅ Provider switching - Working
✅ Chinese language support - Working
✅ GLM-4.5v integration - Working

🚀 Zhipu GLM-4.5v Provider Ready!
```

### **Comprehensive Integration Test:**
```bash
🧪 Comprehensive AI Provider Integration Test
==================================================
🔍 Testing gemini Provider:   ✅ SUCCESS
🔍 Testing openai Provider:   ✅ SUCCESS
🔍 Testing zhipu Provider:    ✅ SUCCESS

🎉 AI Provider Abstraction System: FULLY FUNCTIONAL
   ✅ Easy provider switching through configuration
   ✅ Consistent API across all providers
   ✅ Robust fallback mechanisms
   ✅ Environment-based configuration
   ✅ Programmatic configuration
```

### **Test Coverage:**
- **Provider Creation & Configuration**: All providers can be instantiated with proper credentials
- **API Key Validation**: Each provider validates its required API keys correctly
- **Content Analysis**: All providers implement the required `analyze_content` method
- **Website Generation**: All providers implement the required `generate_website` method
- **Fallback Mechanisms**: Graceful degradation when API services are unavailable
- **Environment Configuration**: Provider switching via environment variables
- **Programmatic Configuration**: Direct provider configuration through code
- **Provider Switching**: Dynamic switching between providers in runtime
- **Language Support**: Multi-language capabilities, especially Chinese for Zhipu

---

## 🎯 **Production Ready Status**