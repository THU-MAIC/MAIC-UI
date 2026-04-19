# Development Setup Guide

This guide will help you set up the Learn Your Way project for local development.

## Prerequisites

- Node.js 18+ and npm
- Python 3.9+
- PostgreSQL (optional, can use SQLite for development)

## Quick Start

1. **Install Dependencies**
   ```bash
   # Install root dependencies
   npm install

   # Install frontend dependencies
   cd frontend && npm install

   # Install backend dependencies
   cd ../backend && pip3 install -r requirements.txt
   ```

2. **Environment Setup**
   ```bash
   # Backend environment
   cd backend
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start Development Servers**
   ```bash
   # From project root
   npm run dev

   # Or start separately:
   # Frontend (port 3000)
   cd frontend && npm run dev

   # Backend (port 8000)
   cd backend && uvicorn main:app --reload
   ```

4. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Project Structure

```
learn-your-way/
├── README.md                 # Project overview
├── DESELOPMENT.md          # This file
├── package.json             # Root package.json with scripts
├── frontend/                # Next.js React application
│   ├── src/
│   │   ├── app/           # App router and pages
│   │   ├── components/     # React components
│   │   ├── hooks/          # Custom React hooks
│   │   └── lib/            # Utility functions
│   ├── public/               # Static assets
│   └── package.json
├── backend/                 # FastAPI Python application
│   ├── src/
│   │   ├── api/           # API routes
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── utils/           # Helper functions
│   ├── uploads/              # File upload directory
│   ├── tests/                # Test files
│   ├── requirements.txt        # Python dependencies
│   └── main.py               # FastAPI application
└── shared/                 # Shared types and utilities
```

## Features Implemented

### ✅ Core Features
- [x] Project structure and development environment
- [x] Next.js frontend with TypeScript
- [x] Python FastAPI backend
- [x] PDF processing service
- [x] Content personalization engine
- [x] 5 Learning modalities:
  - [x] Immersive Text Mode
  - [x] Slides & Narration Mode
  - [x] Audio Lessons Mode
  - [x] Mind Maps Mode
  - [x] Assessment Mode
- [x] User authentication and profiles
- [x] Progress tracking and analytics
- [x] AI integration for content generation
- [x] Responsive design and accessibility features

### 🎯 Frontend Features
- React 18 with Next.js 14
- TypeScript for type safety
- Tailwind CSS for styling
- 5 learning mode components
- Accessibility panel with settings
- Responsive design for mobile/tablet/desktop
- Screen reader support
- Keyboard navigation
- High contrast mode
- Text-to-speech integration

### 🔧 Backend Features
- FastAPI with Python
- JWT authentication
- PDF processing with pdfplumber and PyPDF2
- Content personalization engine
- Assessment generation
- RESTful API design
- Database models for content and users
- File upload handling
- Error handling and logging

### 🛠 Architecture Components

1. **PDF Processing Pipeline**
   - Text extraction and structure analysis
   - Metadata extraction
   - Section identification
   - Key concept extraction
   - Readability scoring

2. **Personalization Engine**
   - Grade-level adaptation
   - Interest-based example replacement
   - Cultural relevance application
   - Learning mode optimization

3. **Assessment System**
   - Multiple question types (MCQ, True/False, Drag-Drop, Fill-in-blanks)
   - Dynamic difficulty adjustment
   - Performance analytics
   - Personalized feedback

4. **Learning Modalities**
   - Immersive Text with embedded interactions
   - Slides with narration support
   - Audio lessons with dialogue simulation
   - Interactive mind maps
   - Comprehensive assessments

## Development Scripts

### Available Scripts
```bash
# Development
npm run dev                    # Start both frontend and backend
npm run dev:frontend           # Frontend only
npm run dev:backend            # Backend only

# Building
npm run build                  # Build both frontend and backend
npm run build:frontend         # Build frontend only
npm run build:backend           # Build backend only

# Testing
npm run test                    # Run all tests
npm run test:frontend           # Run frontend tests
npm run test:backend            # Run backend tests

# Utilities
npm run install:all            # Install all dependencies
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user
- `GET /api/auth/verify-token` - Verify token validity

### PDF Processing
- `POST /api/pdf/upload` - Upload and process PDF
- `GET /api/pdf/documents` - Get user documents
- `GET /api/pdf/documents/{id}` - Get specific document
- `POST /api/pdf/documents/{id}/extract-content` - Extract personalized content

### Content
- `GET /api/content/sections` - Get content sections
- `POST /api/content/personalize` - Personalize content
- `GET /api/content/search` - Search content

### Assessments
- `POST /api/assessments/generate` - Generate quiz
- `POST /api/assessments/submit` - Submit quiz answers
- `GET /api/assessments/progress` - Get assessment progress

## Testing

### Frontend Tests
```bash
cd frontend
npm test                    # Run tests
npm run test:watch         # Watch mode
npm run test:coverage       # Coverage report
```

### Backend Tests
```bash
cd backend
python -m pytest           # Run tests
python -m pytest -v        # Verbose output
python -m pytest --cov   # With coverage
```

## Database Setup

### Development Database (SQLite)
```bash
cd backend
# SQLite will be created automatically
python main.py
```

### Production Database (PostgreSQL)
1. Install PostgreSQL
2. Create database:
   ```sql
   CREATE DATABASE learn_your_way;
   ```
3. Update `.env` file:
   ```
   DATABASE_URL=postgresql://username:password@localhost/learn_your_way
   ```

## Environment Variables

### Backend (.env)
```env
DATABASE_URL=postgresql://user:password@localhost/learn_your_way
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-key (optional)
DEBUG=True
```

### Frontend
No environment variables needed for basic development.

## Deployment

### Frontend (Vercel/Netlify)
```bash
cd frontend
npm run build
# Deploy the .next folder
```

### Backend (Heroku/Railway)
```bash
cd backend
pip3 install -r requirements.txt
# Set environment variables
# Deploy to your preferred platform
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a pull request

## Troubleshooting

### Common Issues

1. **Frontend build fails**
   ```bash
   rm -rf .next node_modules
   npm install
   npm run build
   ```

2. **Backend imports fail**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Database connection fails**
   - Check DATABASE_URL in .env
   - Ensure PostgreSQL is running
   - Verify database exists

4. **PDF processing fails**
   - Check file permissions in uploads/
   - Ensure PDF is not corrupted
   - Check file size limits

## Performance Considerations

- PDF processing is CPU-intensive
- Consider using background tasks for production
- Implement file cleanup for old uploads
- Add caching for frequently accessed content
- Optimize database queries with proper indexing

## Security Notes

- JWT tokens should have reasonable expiration
- File uploads should be validated
- Input sanitization is crucial
- Rate limiting for API endpoints
- HTTPS in production
- Environment variables should be secure

## Future Enhancements

- [ ] Real-time collaboration features
- [ ] Advanced AI-powered content generation
- [ ] Video content support
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Integration with LMS systems
- [ ] Offline content synchronization
- [ ] Mobile app development