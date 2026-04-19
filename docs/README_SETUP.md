# Learn Your Way - Authentication System Setup

This document provides step-by-step instructions to set up and test the authentication system for Learn Your Way.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+
- Git

### 1. Install Dependencies

```bash
# Install all dependencies (frontend and backend)
npm run install:all
```

### 2. Set Up Backend Environment

```bash
cd backend
cp .env.example .env
```

Edit the `.env` file if needed:
```env
DATABASE_URL=sqlite:///./learn_your_way.db
SECRET_KEY=your-super-secret-key-change-this
DEBUG=True
```

### 3. Start Development Servers

```bash
# From the project root - starts both frontend and backend
npm run dev
```

Or start them separately:

```bash
# Backend (port 8000)
cd backend && uvicorn main:app --reload

# Frontend (port 3000)
cd frontend && npm run dev
```

### 4. Test the Authentication System

The backend will be available at: http://localhost:8000
The frontend will be available at: http://localhost:3000

#### Automated Backend Test:
```bash
python3 test_auth.py
```

#### Manual Testing:

1. **Frontend Registration:**
   - Go to http://localhost:3000/register
   - Create a new account

2. **Frontend Login:**
   - Go to http://localhost:3000/login
   - Sign in with your credentials

3. **Backend API Documentation:**
   - Go to http://localhost:8000/docs
   - Test API endpoints directly

## 📁 Project Structure

```
learn-your-way/
├── backend/                 # FastAPI Python application
│   ├── src/
│   │   ├── api/            # API routes (auth, pdf, content, assessments)
│   │   ├── core/           # Database and security configuration
│   │   └── models/         # SQLAlchemy database models
│   ├── uploads/            # File upload directory
│   └── main.py             # FastAPI application entry point
├── frontend/               # Next.js React application
│   ├── src/
│   │   ├── app/            # App router pages
│   │   ├── components/     # React components
│   │   └── lib/            # Utilities and API client
│   └── package.json
└── package.json            # Root package with scripts
```

## 🔐 Authentication Features Implemented

### Backend (FastAPI)
- ✅ User registration with validation
- ✅ User login with JWT tokens
- ✅ Password hashing with bcrypt
- ✅ Token-based authentication middleware
- ✅ Protected endpoints
- ✅ User profile management

### Frontend (Next.js)
- ✅ Login and registration forms
- ✅ Authentication context and state management
- ✅ Protected routes
- ✅ Token storage in cookies
- ✅ Automatic logout on token expiration
- ✅ Form validation with Zod

## 🔧 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/verify-token` - Verify token validity
- `POST /api/auth/logout` - Logout endpoint

### Users Database Schema
- `id` - Primary key
- `email` - Unique email address
- `username` - Unique username
- `hashed_password` - Bcrypt hashed password
- `full_name` - Optional full name
- `grade_level` - K-12 grade level (0 for Kindergarten)
- `interests` - JSON list of user interests
- `learning_preferences` - JSON object of learning preferences
- `is_active` - Boolean active status
- `created_at` - Registration timestamp

## 🛠 Development Commands

```bash
# Development (runs both frontend:3000 and backend:8000)
npm run dev

# Frontend only
npm run dev:frontend

# Backend only
npm run dev:backend

# Install all dependencies
npm run install:all

# Run tests
npm run test

# Backend tests only
npm run test:backend

# Frontend tests only
npm run test:frontend
```

## 🔍 Testing

### Backend API Testing
The test script `test_auth.py` covers:
1. User registration
2. User login
3. Protected endpoint access
4. Token verification
5. Logout functionality

Run it with: `python3 test_auth.py`

### Frontend Testing
Test the following flows manually:
1. Visit `/register` and create an account
2. Verify you're redirected to `/dashboard`
3. Logout and visit `/login`
4. Verify you can't access `/dashboard` while logged out
5. Test form validation for invalid inputs

## 🐛 Troubleshooting

### Common Issues

1. **Backend won't start:**
   ```bash
   cd backend
   pip3 install -r requirements.txt
   ```

2. **Frontend build errors:**
   ```bash
   cd frontend
   rm -rf .next node_modules
   npm install
   npm run build
   ```

3. **Database connection issues:**
   - Check `DATABASE_URL` in backend/.env
   - Ensure the database directory is writable

4. **CORS errors:**
   - Verify frontend is running on localhost:3000
   - Backend CORS is configured for localhost:3000

5. **JWT token issues:**
   - Check SECRET_KEY in backend/.env
   - Clear browser cookies and re-authenticate

## 📚 Next Steps

The authentication system is fully functional. The next development phases would include:

1. **PDF Upload Integration**
2. **Content Management System**
3. **Learning Mode Components**
4. **Assessment System**
5. **Progress Tracking**

Each area has a complete backend API structure ready for implementation.

## 🔐 Security Notes

- Passwords are hashed using bcrypt
- JWT tokens have configurable expiration
- CORS is properly configured
- Input validation on all endpoints
- SQL injection protection via SQLAlchemy ORM
- Environment variables for sensitive configuration