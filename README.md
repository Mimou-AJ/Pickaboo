# Pickaboo - AI-Powered Gift Recommendation System

An intelligent gift recommendation platform that uses AI agents to understand recipients and suggest personalized gifts based on their preferences, budget, and occasion.

## 🎁 Features

- **AI-Powered Question Generation**: Intelligent detective agent generates targeted questions to understand gift recipients
- **Persona Building**: Create detailed recipient profiles with age, gender, relationship, occasion, and budget
- **Smart Recommendations**: Get personalized gift suggestions based on AI analysis of answers
- **Budget-Aware**: Four predefined budget ranges (Under 25€, 25-50€, 50-100€, Over 100€)
- **Public Access**: No authentication required - start finding gifts immediately

## 🏗️ Architecture

Built with clean architecture principles:

- **Domain Layer**: Core entities (Persona, Question, Answer)
- **Application Layer**: Business logic and AI agent integration
- **Infrastructure Layer**: 
  - FastAPI REST API
  - SQLAlchemy ORM with PostgreSQL
  - Pydantic-AI for intelligent agents
  - Rate limiting
- **Testing**: Comprehensive pytest unit and integration tests

## 🚀 Quick Start

### Prerequisites

1. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   
2. **Configure your `.env` file**:
   - `HF_TOKEN`: Get your HuggingFace API token from [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
   - `DATABASE_URL`: Database connection string (default works with Docker)
   - `POSTGRES_*`: PostgreSQL credentials (defaults are fine for local development)

### Using Docker (Recommended)

1. Install Docker Desktop
2. Run the application:
```bash
docker compose up --build
```
3. API available at `http://localhost:8000`
4. Stop services:
```bash
docker compose down
```

### Local Development (Without Docker)

1. Install dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Configure SQLite (optional for development):
   - In `src/database/core.py`, change `DATABASE_URL` to use SQLite

3. Run the application:
```bash
uvicorn src.main:app --reload
```

## 🧪 Testing

Run all tests:
```bash
pytest
```

Run specific test files:
```bash
pytest tests/test_questions_service.py
pytest tests/test_recommendations.py
```

## 📋 API Endpoints

### Personas
- `POST /personas` - Create a new recipient persona
- `GET /personas/{id}` - Get persona details

### Questions
- `GET /personas/{id}/questions` - Generate AI-powered questions for a persona
- `POST /questions/answers` - Submit bulk answers

### Recommendations
- `GET /personas/{id}/recommendations` - Get personalized gift recommendations

## 🤖 AI Agents

The system uses two AI agents powered by pydantic-ai:

1. **Gift Detective**: Generates smart questions based on recipient profile (age, gender, occasion, relationship, budget)
2. **Gift Recommendation Agent**: Analyzes answers and persona to suggest perfect gifts

## 💾 Database Schema

- **Personas**: Recipient profiles with demographics and budget
- **Questions**: AI-generated questions with multiple-choice options (stored as JSONB)
- **Answers**: User responses linked to questions
- **Recommendations**: Generated gift suggestions

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **Database**: PostgreSQL 17
- **ORM**: SQLAlchemy
- **AI**: Pydantic-AI with HuggingFace models
- **Validation**: Pydantic v2
- **Testing**: Pytest
- **Containerization**: Docker & Docker Compose

## 📦 Project Structure

```
Pickaboo/
├── src/
│   ├── auth/                 # (Removed - no longer needed)
│   ├── build_persona/        # Persona creation and management
│   ├── questions/            # Question generation and answers
│   ├── questions_agent/      # AI detective agent
│   ├── recommendations/      # Gift recommendation logic
│   ├── database/             # Database configuration
│   └── main.py               # FastAPI application
├── tests/                    # Unit and integration tests
├── docker-compose.yml        # Docker services configuration
├── Dockerfile                # Application container
└── requirements.txt          # Python dependencies
```




---

**Happy Gift Hunting! 🎉**