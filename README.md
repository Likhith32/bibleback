# Galilee Workspace API (Backend)

The backend for Galilee Workspace, an AI-powered Bible study platform. Built with **FastAPI** and integrated with **Google Gemini** for intelligent scripture analysis.

## 🚀 Features

- **Smart Search**: Semantic and keyword-based search for English and Telugu scriptures.
- **AI Bible Insights**: Deep theological analysis and sermon generation using Google Gemini.
- **Daily Content**: Automated daily bread, verses, and devotions.
- **Document Export**: Generate PDF and Word documents for study notes.
- **Suggestions**: Real-time search suggestions and cross-references.

## 🛠 Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Database**: PostgreSQL (with PostGIS for future geospatial mapping)
- **AI**: [Google Gemini Pro AI](https://ai.google.dev/)
- **Libraries**: Pydantic, reportlab (PDF), python-docx (Word), uvicorn.

## ⚙️ Setup & Installation

### 1. Prerequisites
- Python 3.10+
- PostgreSQL database

### 2. Environment Configuration
Create a `.env` file in the root of the `bible-backend/` directory:
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/bible_db
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Running the Server
```bash
uvicorn app.main:app --reload
```
The API will be available at `http://127.0.0.1:8000`.

## 📖 API Documentation
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

---
*Powered by Galilee Study Tools.*
