# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

Learn Your Way is a full-stack monorepo with a **well-structured backend** that needs **frontend integration**. The system transforms PDFs into personalized learning experiences across 5 modalities.

**Critical Context**: The backend API is comprehensive and functional, but the frontend operates entirely on static mock data. The primary development task is bridging this disconnect.

### Technology Stack
- **Backend**: python3  FastAPI, SQLAlchemy ORM, SQLite (dev) / PostgreSQL (prod)
- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS, Axios (installed but unused)
- **AI Integration**: OpenAI API for content personalization and assessment generation
- **PDF Processing**: PyPDF2, pdfplumber for text extraction and structure analysis

### Core Architecture Pattern
```
PDF Upload → Processing Pipeline → Content Extraction → Personalization → Multi-Modal Generation → Learning Modes
```

**Five Learning Modalities**:
1. **Immersive Text**: Interactive textbook with embedded questions and AI-generated images
2. **Slides & Narration**: Presentation-style content with optional AI narration
3. **Audio Lessons**: Simulated teacher-student conversations with dialogue
4. **Mind Maps**: Hierarchical knowledge visualization with expandable nodes
5. **Assessments**: Quiz system with Bloom's taxonomy levels and progress tracking

## Development Commands

### Project Setup
```bash
# Install all dependencies
npm run install:all

# Development (runs both frontend:3000 and backend:8000)
npm run dev

# Production build
npm run build

# Testing
npm run test
```

### Backend Development
```bash
cd backend
pip3 install -r requirements.txt
python3  main.py                    # Start FastAPI server (port 8000)
uvicorn main:app --reload        # Development server with hot reload
python3  -m pytest                 # Run backend tests
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev                        # Start Next.js dev server (port 3000)
npm run build                      # Production build
npm run test                       # Run React tests (Jest setup ready)
```

### Database
- SQLite database: `learn_your_way.db` (auto-created on first run)
- Models auto-created via SQLAlchemy in `backend/src/core/database.py`
- Tables: Users, Documents, ContentSections, PersonalizedContent, LearningProgress

## Key Integration Points

### 1. PDF Processing Pipeline
**Backend**: Complete service in `backend/src/api/pdf_processing.py`
- Endpoint: `POST /api/pdf/upload` (multipart/form-data)
- Processing: PDF → text extraction → section identification → content analysis
- Storage: File saved to `uploads/` directory, processed JSON saved alongside

**Frontend**: Mock upload in `frontend/src/app/page.tsx:32-38`
- **Missing**: Actual API call to upload endpoint
- **Missing**: Progress tracking during processing
- **Missing**: Error handling and file validation

### 2. Content Management & Personalization
**Backend**: Full CRUD in `backend/src/api/content.py`
- Endpoints: `/api/content/sections`, `/api/content/personalize`
- Personalization engine: `backend/src/services/personalization_service.py`
- Supports: Grade-level adaptation, interest-based content, cultural relevance

**Frontend**: Static content in all learning mode components
- **Missing**: Dynamic content loading from backend
- **Missing**: User preference collection and storage
- **Missing**: Learning mode switching with personalized data

### 3. Assessment System
**Backend**: Quiz generation and grading in `backend/src/api/assessments.py`
- Assessment generator: `backend/src/services/assessment_service.py`
- Support for multiple question types, difficulty levels, feedback generation

**Frontend**: Basic quiz components in `frontend/src/components/learning-modes/AssessmentMode.tsx`
- **Missing**: Real quiz generation from backend
- **Missing**: Quiz submission and grading integration
- **Missing**: Progress tracking and analytics

### 4. Authentication Framework
**Backend**: Structure exists in `backend/src/api/auth.py` but implementation incomplete
- **Missing**: User registration, login/logout functionality
- **Missing**: JWT token management and validation

**Frontend**: No authentication components or state management
- **Missing**: Login/register forms
- **Missing**: Protected route handling
- **Missing**: User session management

## Database Schema Relationships

```
Users (1) → (N) Documents
Users (1) → (N) PersonalizedContent
Users (1) → (N) LearningProgress
Documents (1) → (N) ContentSections
ContentSections (1) → (N) PersonalizedContent
```

**Key Tables**:
- **Users**: grade_level (K-12), interests (JSON), learning_preferences (JSON)
- **Documents**: PDF metadata, processing status, public/private flag
- **ContentSections**: Extracted sections with key concepts and learning objectives
- **PersonalizedContent**: Mode-specific adaptations with personalization metadata
- **LearningProgress**: User progress tracking, quiz scores, time spent

## File Structure Patterns

### Backend Service Layer
- `/backend/src/api/*.py`: API route definitions with FastAPI routers
- `/backend/src/services/*.py`: Business logic (PDF processing, personalization, assessment)
- `/backend/src/models/*.py`: SQLAlchemy ORM models
- `/backend/src/core/`: Database configuration and shared utilities

### Frontend Component Architecture
- `/frontend/src/components/learning-modes/*.tsx`: Five learning mode implementations
- `/frontend/src/hooks/*.ts`: Custom React hooks (accessibility, responsive)
- `/frontend/src/components/ui/*.tsx`: Shared UI components (ProgressBar, LoadingSpinner)

## Development Priorities

### Phase 1: Foundation (Weeks 1-2)
1. **API Service Layer**: Create `/frontend/src/services/api.ts` for backend communication
2. **Authentication Flow**: Implement user registration, login, JWT token management
3. **PDF Upload Integration**: Connect `frontend/src/app/page.tsx:32-38` to `/api/pdf/upload`
4. **Error Handling**: Add loading states, error boundaries, proper user feedback

### Phase 2: Core Integration (Weeks 3-4)
1. **Content Loading**: Replace static mock data in learning modes with dynamic API calls
2. **Personalization Integration**: Connect user preferences to backend personalization engine
3. **Assessment Integration**: Implement real quiz generation and submission
4. **Progress Tracking**: Connect learning progress to database analytics

### Phase 3: Advanced Features (Weeks 5-6)
1. **Real-time Updates**: WebSocket support for PDF processing progress
2. **Advanced AI Features**: OpenAI integration for content generation and illustrations
3. **Performance Optimization**: Caching, lazy loading, state management
4. **Mobile Optimization**: Responsive design improvements and mobile-specific features

## Critical Implementation Notes

### API Integration Architecture
- **Base URL**: `http://localhost:8000` (configured in CORS)
- **Authentication**: JWT tokens (framework exists, needs frontend implementation)
- **Error Handling**: FastAPI returns structured error responses with status codes
- **File Uploads**: Multipart form data with proper validation and size limits

### Content Personalization Pipeline
1. **Grade-Level Adaptation**: Language complexity adjustment based on user grade
2. **Interest Substitution**: Replace generic examples with user-specific content
3. **Cultural Relevance**: Adapt contexts to learner background
4. **Progress-Based Adjustment**: Modify difficulty based on performance

### Assessment Generation Pattern
- **Bloom's Taxonomy**: Questions at different cognitive levels
- **Multiple Question Types**: Multiple choice, true/false, drag-and-drop
- **Automatic Feedback**: Personalized improvement suggestions
- **Progress Analytics**: Strength/growth area analysis

### PDF Processing Workflow
1. **Upload**: File validation, unique filename generation, database record creation
2. **Processing**: Background processing with PyPDF2/pdfplumber
3. **Section Extraction**: Automatic identification of chapters and key concepts
4. **Content Analysis**: Learning objective extraction and metadata generation
5. **Storage**: Processed JSON alongside original file for quick access

## Testing Strategy

### Backend Testing
```bash
cd backend/test
python3  -m pytest                       # Run all tests
python3  -m pytest test_pdf_processing.py   # Test specific module
```

### Frontend Testing
```bash
cd frontend
npm test                                # Run Jest tests
npm run test --watch                   # Watch mode
```

### Integration Testing
- **API Testing**: Test all endpoints with sample data
- **PDF Upload Testing**: Verify file processing pipeline end-to-end
- **Authentication Testing**: Verify JWT token lifecycle and protected routes
- **Content Loading Testing**: Ensure personalization pipeline works correctly

## Security Considerations

- **File Upload Validation**: PDF only, size limits, malware scanning
- **SQL Injection Protection**: SQLAlchemy ORM provides protection
- **JWT Security**: Proper token expiration, refresh token flow
- **CORS Configuration**: Currently localhost only, needs production domains
- **Input Sanitization**: Validate all user inputs and content personalization parameters

## Performance Optimization

- **Database Queries**: Use proper indexing on foreign keys and frequently queried fields
- **Content Caching**: Cache processed content to avoid repeated personalization
- **Lazy Loading**: Load learning mode content on-demand
- **File Storage**: Consider cloud storage for production (AWS S3 mentioned in plans)
- **API Response Times**: Implement pagination and response size limits

## Common Development Tasks

When implementing features, always follow the **backend-first integration** pattern:
1. **Verify backend endpoint exists** and test with API client
2. **Create frontend API service function** with proper error handling
3. **Implement loading states** and error boundaries
4. **Connect to UI components** with proper TypeScript types
5. **Test integration end-to-end** with real backend data

The foundation is solid - focus on **integration** rather than building new infrastructure.