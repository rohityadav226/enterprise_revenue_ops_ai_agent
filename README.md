# Enterprise Revenue & Operations AI Agent

An enterprise-oriented backend application built with **Python, FastAPI and PostgreSQL**, designed as the foundation for an AI-powered business intelligence and operations assistant.

The application provides structured APIs for customer management, product information, business metrics and sales analysis requests. It follows a modular architecture that can be extended with Large Language Models (LLMs), Retrieval-Augmented Generation (RAG) and Agentic AI workflows.

> **Project status:** In active development. Currently implementing the backend and database foundation as part of a 60-day Applied AI Engineering learning roadmap.

---

## Overview

The goal of this project is to develop an AI assistant that enables employees to interact with enterprise business data using natural language.

The planned system will allow users to:

- Retrieve customer and product information.
- Analyse business metrics and revenue performance.
- Ask questions about business operations using natural language.
- Retrieve relevant information from internal company documents.
- Execute controlled, multi-step workflows through AI agents.
- Receive structured, evidence-based responses.

The current implementation focuses on the backend architecture, API development, request validation and PostgreSQL integration.

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| FastAPI | REST API development |
| Pydantic | Request validation and response schemas |
| PostgreSQL | Relational database |
| SQLAlchemy 2.x | Database ORM and queries |
| Psycopg | PostgreSQL database driver |
| python-dotenv | Environment variable management |
| Git | Version control |

## Architecture

The application follows a modular, layered architecture that separates API routing, data validation, business logic and database operations.

```text
                    Client / Frontend
                           |
                           v
                    FastAPI Application
                           |
                           v
                     API Routers
                           |
                +----------+----------+
                |                     |
                v                     v
             Schemas              Services
                |                     |
                |                     v
                |              Database Operations
                |                     |
                |                     v
                |                SQLAlchemy
                |                     |
                +---------------------+
                                      |
                                      v
                                 PostgreSQL
```

### Project Structure

```text
enterprise-ai-agent/
│
├── app/
│   │
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── seed.py
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   └── mock_data.py
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── system.py
│   │   ├── customers.py
│   │   ├── products.py
│   │   └── analytics.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── catalog.py
│   │   └── analytics.py
│   │
│   └── services/
│       ├── __init__.py
│       ├── catalog_service.py
│       └── analytics_service.py
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Current Features

### 1. REST API Development
- FastAPI application setup.
- GET and POST endpoints.
- Path and query parameters.
- JSON request and response handling.
- Interactive API documentation through Swagger UI.

### 2. Data Validation
- Pydantic request and response models.
- Field-level validation.
- Type validation and restricted input values.
- Cross-field validation using model validators.
- Appropriate HTTP error responses.

### 3. Database Integration
- PostgreSQL database connectivity.
- SQLAlchemy 2.x ORM.
- Declarative database models.
- Database session management.
- Dependency injection for database sessions.
- Database seeding with sample business records.

### 4. Business Data Operations
- Customer record retrieval.
- Product information retrieval.
- Revenue and order metrics.
- Filtering metrics by reporting period and region.
- Structured sales analysis requests.

## API Endpoints

The following endpoints are currently implemented.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check application health |
| GET | `/about` | Retrieve application information |
| GET | `/customers/{customer_id}` | Retrieve customer information |
| GET | `/products/{product_id}` | Retrieve product information |
| GET | `/metrics` | Retrieve business metrics |
| POST | `/analysis` | Submit a business analysis request |
| POST | `/sales-analysis` | Submit a validated sales analysis request |

### Example: Retrieve a Customer

```http
GET /customers/101
```

Response:

```json
{
  "customer_id": 101,
  "name": "Aarav Sharma",
  "segment": "Enterprise"
}
```

### Example: Filter Business Metrics

```http
GET /metrics?period=monthly&region=north
```

### Example: Submit a Sales Analysis Request

```http
POST /sales-analysis
Content-Type: application/json
```

```json
{
  "start_date": "2026-10-01",
  "end_date": "2026-10-31",
  "minimum_revenue": 500000,
  "region": "north",
  "analysis_type": "revenue",
  "notes": "Investigate monthly revenue performance"
}
```

The endpoint validates the submitted parameters and returns the structured request information.

## Getting Started

### Prerequisites

- Python 3.10 or newer
- PostgreSQL
- Git

### 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>

cd enterprise-ai-agent
```

### 2. Create a Virtual Environment

```bash
python3 -m venv .venv

source .venv/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure PostgreSQL

Create a PostgreSQL database and application user.

Example:

```sql
CREATE ROLE ai_agent_user
WITH LOGIN PASSWORD 'your_local_password';

CREATE DATABASE enterprise_ai
OWNER ai_agent_user;
```

### 5. Configure Environment Variables

Create a `.env` file in the project root.

```env
DATABASE_URL=postgresql+psycopg://ai_agent_user:your_local_password@localhost:5432/enterprise_ai
```

Never commit your actual `.env` file or database credentials to GitHub.

### 6. Initialize the Database

Create the database tables and insert the initial sample records:

```bash
python -m app.seed
```

### 7. Start the FastAPI Application

```bash
fastapi dev app/main.py
```

The API will be available at:

```text
http://127.0.0.1:8000
```

### 8. Access API Documentation

Interactive Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

Alternative ReDoc documentation:

```text
http://127.0.0.1:8000/redoc
```

## Development Roadmap

The project is being developed incrementally toward a production-oriented enterprise AI application.

| Phase | Planned Development |
|---|---|
| Backend Engineering | FastAPI, modular architecture, validation and API testing |
| Database Engineering | PostgreSQL, SQLAlchemy, database migrations and transactions |
| Authentication | JWT, authentication and role-based access control |
| LLM Integration | LLM APIs, structured outputs and function calling |
| Retrieval-Augmented Generation | Embeddings, vector databases and grounded responses |
| Agentic AI | LangGraph, tool calling, state management and MCP |
| Human-in-the-Loop | Approval workflows and controlled agent actions |
| AI Evaluation | Retrieval evaluation, agent evaluation and reliability testing |
| Production Engineering | Docker, AWS, CI/CD, monitoring and observability |
| Security | Prompt injection protection, data access controls and audit logging |

## Engineering Principles

The project aims to follow these principles as it evolves:

- Modular and maintainable application architecture.
- Separation of API, business logic and data access.
- Input validation and structured responses.
- Secure database and credential management.
- Testable and reusable application components.
- Controlled AI tool execution and human approval.
- Reliability, observability and production readiness.

---

**Project:** Enterprise Revenue & Operations AI Agent  
**Domain:** Applied AI, Enterprise Automation and Agentic AI  
**Status:** In active development