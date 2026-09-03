# ATS Resume Score Checker

A production-quality web application that analyzes resumes against job descriptions and generates an ATS-style compatibility score with transparent, explainable criteria.

## Features

- Upload resume (PDF or DOCX) and paste a job description
- Transparent ATS scoring engine (100 points, configurable weights)
- Keyword matching with semantic synonym detection
- Technical skill analysis (matched / missing / additional)
- Resume quality and formatting analysis
- Semantic job relevance using Sentence Transformers
- Actionable, evidence-based suggestions
- User accounts with JWT authentication
- Analysis history management
- Demo mode with sample data
- Privacy-focused (temporary file deletion)

## Tech Stack

**Frontend**: React, Vite, Tailwind CSS, Framer Motion
**Backend**: Python, FastAPI, SQLAlchemy, PostgreSQL
**NLP**: spaCy, scikit-learn, Sentence Transformers
**Processing**: PyMuPDF (PDF), python-docx (DOCX)

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI routes (auth, resume, analysis)
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic (parsing, analysis)
│   │   ├── nlp/           # Keyword extraction, semantic matching
│   │   ├── scoring/       # Transparent scoring engine
│   │   ├── database/      # DB connection & session
│   │   └── utils/         # Auth, file handling
│   ├── tests/             # Unit tests
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/    # Reusable UI components
│       ├── pages/         # Route pages
│       ├── services/      # API client
│       ├── context/       # Auth context
│       └── utils/         # Demo data
├── run.py                 # Dev launcher (starts both backend + frontend)
├── LICENSE                # MIT License
├── docker-compose.yml     # PostgreSQL database
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL (or use Docker)

### Quick Start (Recommended)

The `run.py` launcher starts both the backend and frontend with a single command:

```bash
python run.py            # Start both backend and frontend
python run.py --backend  # Start only the backend
python run.py --frontend # Start only the frontend
```

Press `Ctrl+C` to gracefully stop all services.

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm  # NLP model

# Set up environment
cp .env.example .env
# Edit .env with your database credentials

# Start the server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000` with interactive docs at `/docs`.

### Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env  # Optional: set API URL
npm run dev
```

The app will be available at `http://localhost:5173`.

### Database Setup (Docker)

```bash
docker compose up -d db
```

Or create the database manually:

```bash
createdb ats_resume_checker
```

### Running Tests

```bash
cd backend
pytest
```

## ATS Scoring Engine

The transparent scoring engine allocates 100 points across categories (configurable via environment variables):

| Category | Weight | Criteria |
|----------|--------|----------|
| Keyword Match | 30 | Proportion of job keywords found |
| Technical Skill | 25 | Required technical skills matched |
| Experience Relevance | 20 | Semantic relevance of experience |
| Structure | 10 | Standard sections present |
| Education | 5 | Education info present |
| Formatting | 10 | Readability & parsing quality |

> ⚠️ **Important**: These weights represent an ATS-style compatibility estimate, not the exact algorithm of any specific ATS platform. ATS systems differ significantly.

## Privacy

- Uploaded files are stored temporarily and deleted immediately after analysis
- No resumes are stored in the database
- Analysis results are only associated with your account (if logged in)
- You can delete your analysis history at any time

## License

MIT
