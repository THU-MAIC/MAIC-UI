# API Documentation: Learn Your Way System

## Overview

This document describes the current API structure between the frontend and backend of the Learn Your Way system, as well as identification of what remains to be implemented.

## System Architecture

**Backend:** Python FastAPI application running on port 8000
**Frontend:** Next.js React application running on localhost:3000
**Database:** PostgreSQL with SQLAlchemy ORM
**File Storage:** Local file system with `uploads/` directory

## Current API Endpoints

### 1. Authentication (`/api/auth`)
**Status:** ⚠️ **Framework exists, implementation incomplete**

Current endpoints:
- **Framework structure exists** in `/backend/src/api/auth.py` but implementation is minimal
- Missing actual authentication logic, user registration, login/logout functionality

### 2. PDF Processing (`/api/pdf`)

#### Upload PDF
```http
POST /api/pdf/upload
Content-Type: multipart/form-data
```

**Request Parameters:**
- `file`: PDF file (UploadFile)
- `title`: Document title (string)
- `subject`: Optional subject (string)
- `grade_level`: Optional grade level K-12 (integer)
- `description`: Optional description (string)
- `is_public`: Boolean (default: false)

**Response:**
```json
{
  "id": 1,
  "title": "Document Title",
  "original_filename": "document.pdf",
  "page_count": 25,
  "subject": "Science",
  "grade_level": 6,
  "status": "processing",
  "created_at": "2024-12-03T..."
}
```

#### Get Documents
```http
GET /api/pdf/documents?skip=0&limit=20
```

**Response:** Array of DocumentResponse objects

#### Get Document Details
```http
GET /api/pdf/documents/{document_id}
```

#### Get Processing Status
```http
GET /api/pdf/documents/{document_id}/processing-status
```

**Response:**
```json
{
  "document_id": 1,
  "status": "processing",
  "progress": 50,
  "message": "Extracting content sections..."
}
```

#### Delete Document
```http
DELETE /api/pdf/documents/{document_id}
```

### 3. Content Management (`/api/content`)

#### Get Content Sections
```http
GET /api/content/sections?document_id=1&skip=0&limit=50
```

**Response:**
```json
[
  {
    "id": 1,
    "document_id": 1,
    "title": "Section Title",
    "content": "Section content...",
    "section_type": "chapter",
    "order_index": 1,
    "key_concepts": ["Concept1", "Concept2"],
    "learning_objectives": ["Objective1"],
    "created_at": "2024-12-03T..."
  }
]
```

#### Get Specific Content Section
```http
GET /api/content/sections/{section_id}
```

#### Personalize Content
```http
POST /api/content/personalize
```

**Request Body:**
```json
{
  "content_section_id": 1,
  "learning_mode": "immersive-text",
  "user_preferences": {
    "grade_level": 6,
    "interests": ["space", "science"]
  }
}
```

**Response:**
```json
{
  "id": 1,
  "content_section_id": 1,
  "learning_mode": "immersive-text",
  "personalized_content": {
    "title": "Personalized Title",
    "content": "Adapted content...",
    "interactivities": ["quiz", "simulation"]
  },
  "personalization_metadata": {},
  "grade_level_adapted": 6,
  "created_at": "2024-12-03T..."
}
```

#### Get Personalized Content
```http
GET /api/content/personalized/{section_id}/{learning_mode}
```

#### Search Content
```http
GET /api/content/search?query=solar+system&document_id=1&limit=20
```

### 4. Assessments (`/api/assessments`)

#### Generate Quiz
```http
POST /api/assessments/generate
```

**Request Body:**
```json
{
  "content_section_id": 1,
  "difficulty": "medium",
  "question_count": 5,
  "question_types": ["multiple-choice", "true-false"]
}
```

**Response:**
```json
{
  "id": 1,
  "content_section_id": 1,
  "title": "Solar System Quiz",
  "questions": [
    {
      "id": 1,
      "type": "multiple-choice",
      "question": "What is at the center of our solar system?",
      "options": ["Earth", "The Moon", "The Sun", "Mars"],
      "correct_answer": 2,
      "explanation": "The Sun is at the center..."
    }
  ],
  "difficulty": "medium",
  "estimated_time": 15
}
```

#### Submit Quiz
```http
POST /api/assessments/submit
```

**Request Body:**
```json
{
  "quiz_id": 1,
  "answers": {
    "1": 2,
    "2": 1
  },
  "time_spent": 900
}
```

**Response:**
```json
{
  "quiz_id": 1,
  "score": 85,
  "total_questions": 5,
  "percentage": 0.85,
  "correct_answers": [1, 3],
  "incorrect_answers": [2],
  "time_spent": 900,
  "feedback": {
    "strengths": ["Good understanding of concepts"],
    "areas_for_improvement": ["Review specific topics"]
  },
  "completed_at": "2024-12-03T..."
}
```

#### Get Assessment Progress
```http
GET /api/assessments/progress
```

#### Get Quiz Feedback
```http
GET /api/assessments/feedback/{quiz_id}
```

## Current Frontend-Backend Integration Status

### ❌ **Critical Issue: No API Integration**

The frontend currently contains **no actual API calls** to the backend:

1. **Static Content Only:** All learning modes use hardcoded sample data
2. **Missing HTTP Client:** While `axios` is installed, no API calls are implemented
3. **No State Management:** No global state for API data, authentication, or user progress
4. **Mock PDF Upload:** The upload functionality only sets local state, doesn't call backend

### Frontend Components Status

| Component | API Integration | Status |
|-----------|------------------|---------|
| `page.tsx` | ❌ No API calls for PDF upload | Static mockup only |
| `ImmersiveTextMode.tsx` | ❌ Uses sampleContent object | No backend data |
| `SlidesMode.tsx` | ⚠️ Component exists, likely static | Not reviewed |
| `AudioMode.tsx` | ⚠️ Component exists, likely static | Not reviewed |
| `MindMapMode.tsx` | ⚠️ Component exists, likely static | Not reviewed |
| `AssessmentMode.tsx` | ❌ No API integration for quizzes | Not reviewed |

## Database Schema

### Users Table
```sql
- id (PK)
- email (unique)
- username (unique)
- hashed_password
- full_name
- grade_level (K-12, 0 for Kindergarten)
- interests (JSON)
- learning_preferences (JSON)
- is_active
- created_at, updated_at
```

### Documents Table
```sql
- id (PK)
- title
- original_filename
- file_path
- file_size
- page_count
- subject
- grade_level
- description
- user_id (FK → users.id)
- is_public
- status (processing/ready/error)
- pdf_metadata (JSON)
- created_at, updated_at
```

### Content Sections Table
```sql
- id (PK)
- document_id (FK → documents.id)
- title
- content
- section_type
- order_index
- key_concepts (JSON)
- learning_objectives (JSON)
- section_metadata (JSON)
- created_at, updated_at
```

### Personalized Content Table
```sql
- id (PK)
- content_section_id (FK → content_sections.id)
- user_id (FK → users.id)
- learning_mode
- personalized_content (JSON)
- personalization_metadata (JSON)
- grade_level_adapted
- interests_applied (JSON)
- created_at, updated_at
```

### Learning Progress Table
```sql
- id (PK)
- user_id (FK → users.id)
- document_id (FK → documents.id)
- content_section_id (FK → content_sections.id)
- learning_mode
- status (not_started/in_progress/completed)
- progress_percentage
- time_spent_seconds
- quiz_scores (JSON)
- last_accessed
- progress_metadata (JSON)
- created_at, updated_at
```
