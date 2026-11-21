# Enterprise Revenue Operations AI Agent

<p align="center">
  <strong>An Enterprise AI Assistant for Revenue Intelligence, Sales Analytics and Business Operations</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-Backend-blue?logo=python" />
  <img src="https://img.shields.io/badge/FastAPI-Framework-009688?logo=fastapi" />
  <img src="https://img.shields.io/badge/PostgreSQL-Database-4169E1?logo=postgresql" />
  <img src="https://img.shields.io/badge/SQLAlchemy-ORM-D71F00" />
  <img src="https://img.shields.io/badge/AI-Agentic_AI-purple" />
  <img src="https://img.shields.io/badge/Status-In_Development-orange" />
</p>

---

## Overview

The **Enterprise Revenue Operations AI Agent** is an enterprise-oriented Applied AI project designed to help B2B companies analyse sales performance, understand revenue operations and automate business workflows through natural-language interactions.

The system is being developed around a fictional B2B SaaS company, NexusFlow Technologies.

The long-term objective is to build an AI assistant capable of retrieving enterprise business information, analysing sales pipeline and bookings, searching internal documentation, identifying business risks and executing approved operational workflows.

The application is being developed using Python, FastAPI, PostgreSQL, SQLAlchemy, LLMs, Retrieval-Augmented Generation (RAG) and Agentic AI orchestration.

> **Project status:** Active development. The current development stage focuses on backend engineering, PostgreSQL integration, authentication, automated testing and the RevOps database architecture. LLM integration, RAG and agent orchestration are planned development phases.

## Project Objectives

The system aims to enable business employees to:

- Analyse revenue bookings across different reporting periods.
- Monitor sales pipeline and weighted pipeline.
- Evaluate salesperson performance against assigned targets.
- Identify stalled opportunities and potential business risks.
- Retrieve customer account and opportunity information.
- Search internal sales policies and business documents.
- Ask business questions using natural language.
- Generate evidence-based management reports.
- Propose operational actions with appropriate human approval.

## Business Domain

The application focuses on B2B Revenue Operations (RevOps), connecting sales performance, business intelligence and operational workflows.

The underlying business scenario represents a fictional enterprise software company with multiple sales regions, representatives, customer accounts, products and commercial opportunities.

### Core Business Entities

| Entity | Description |
|---|---|
| Users | Internal employees, managers, analysts and administrators |
| Accounts | Companies purchasing enterprise software |
| Contacts | Individuals associated with customer accounts |
| Products | Enterprise software products and subscription offerings |
| Opportunities | Potential commercial sales deals |
| Opportunity Line Items | Products, quantities and negotiated prices within deals |
| Sales Activities | Calls, meetings, demonstrations and follow-up tasks |
| Sales Targets | Sales quotas assigned to employees |
| Bookings | Confirmed closed-won commercial deals |

## Planned System Architecture

The intended architecture separates the API layer, business logic, database access and AI orchestration.

```text
                    Business Users
                          |
                          v
                  FastAPI Application
                          |
                 Authentication / RBAC
                          |
                          v
                  LangGraph Agent
                          |
             +------------+------------+
             |            |            |
             v            v            v
        Analytics       RAG          MCP Tools
         Tools        Retrieval      Integration
             |            |            |
             v            v            v
        PostgreSQL    pgvector     Business APIs
             |            |
             +------------+
                   |
                   v
          Evidence-Based Responses
                   |
                   v
          Human-Approved Actions
```

The AI agent will access company information through predefined, permission-controlled tools rather than unrestricted database access.

## Technology Stack

### Backend Engineering

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| FastAPI | REST API development |
| Pydantic | Request and response validation |
| SQLAlchemy 2.x | Object Relational Mapping |
| PostgreSQL | Relational database |
| Psycopg | PostgreSQL database driver |
| Alembic | Database schema migrations |

### Security and Testing

| Technology | Purpose |
|---|---|
| JWT | Authentication tokens |
| Argon2 | Password hashing |
| FastAPI Dependencies | Authentication and authorization |
| Role-Based Access Control | Permission management |
| pytest | Automated testing |
| HTTPX | API testing |

### Planned Applied AI Stack

| Technology | Purpose |
|---|---|
| LLM APIs | Natural-language understanding and generation |
| Embeddings | Semantic document representation |
| pgvector | Vector storage and similarity search |
| RAG | Retrieval-Augmented Generation |
| LangGraph | Stateful agent orchestration |
| MCP | Standardized tool and context integration |

### Production Engineering

| Technology | Purpose |
|---|---|
| Docker | Application containerization |
| GitHub Actions | Continuous Integration |
| AWS | Cloud infrastructure |
| ECS Fargate | Container deployment |
| RDS PostgreSQL | Managed relational database |
| CloudWatch | Logging and monitoring |

## Development Progress

The project is being developed incrementally through a structured 60-day engineering roadmap.

| Days | Development Area | Status |
|---|---|---|
| 1–2 | Python setup, HTTP fundamentals and FastAPI | Completed |
| 3 | Pydantic validation and exception handling | Completed |
| 4 | Modular application architecture | Completed |
| 5 | PostgreSQL and SQLAlchemy integration | Completed |
| 6 | JWT authentication and role-based access control | Completed |
| 7 | Automated API testing | Completed |
| 8 | CRUD operations, transactions and pagination | Completed |
| 9 | RevOps business requirements and domain modelling | Completed |
| 10 | Entity Relationship Diagram and database design | Completed |
| 11 | SQLAlchemy RevOps models and relationships | In Progress |
| 12 | Alembic migrations and database restructuring | Planned |
| 13–14 | Synthetic business data and database validation | Planned |
| 15–21 | SQL analytics and RevOps business metrics | Planned |
| 22–28 | LLM engineering and model integration | Planned |
| 29–35 | Retrieval-Augmented Generation | Planned |
| 36–42 | LangGraph and Agentic AI workflows | Planned |
| 43–49 | MCP, AI evaluation, security and reliability | Planned |
| 50–56 | Docker, AWS and production deployment | Planned |
| 57–60 | Integration, documentation and portfolio release | Planned |

## Current Backend Capabilities

The existing backend foundation includes:

- Modular FastAPI application architecture.
- REST API development with GET and POST endpoints.
- Path parameters, query parameters and JSON request bodies.
- Pydantic request and response validation.
- PostgreSQL database connectivity.
- SQLAlchemy ORM and database sessions.
- JWT-based user authentication.
- Password hashing using Argon2.
- Role-based authorization.
- Dependency injection for database and authentication.
- Product CRUD operations and pagination.
- Database transactions and rollback handling.
- Automated API tests using pytest and HTTPX.

The project is currently transitioning its original sample data model into a dedicated B2B Revenue Operations database schema.

## RevOps Business Metrics

The analytics layer is planned around the following business metrics.

| Metric | Definition |
|---|---|
| Open Pipeline | Total value of open sales opportunities |
| Weighted Pipeline | Opportunity value adjusted by win probability |
| Bookings | Value of qualifying closed-won commercial commitments |
| Win Rate | Closed-won deals divided by all closed opportunities |
| Quota Attainment | Actual bookings divided by assigned sales target |
| Average Deal Size | Average value of closed-won bookings |
| Sales Cycle | Average time taken to close successful opportunities |

These metrics will be calculated from underlying business records rather than maintained as independent sources of truth.

## Planned AI Agent Capabilities

### 1. Revenue Intelligence

Example question:

"Compare October and November bookings by region and identify the largest changes."

The agent will retrieve the relevant records, calculate the differences and provide an evidence-based explanation.

### 2. Sales Pipeline Intelligence

Example question:

"Show me our weighted pipeline for the next quarter."

The agent will retrieve open opportunities, calculate weighted values and summarise pipeline performance.

### 3. Account Intelligence

Example question:

"Give me a summary of Acme Technologies, including its opportunities and recent sales activities."

The agent will combine account, opportunity and activity information.

### 4. Enterprise Knowledge Retrieval

Example question:

"What is our approval policy for discounts above 20%?"

The agent will retrieve information from internal documents using RAG and provide source references.

### 5. Agentic Workflow Automation

Example question:

"Identify stalled opportunities and prepare follow-up tasks for their owners."

The agent will identify relevant opportunities, propose appropriate actions and request human approval before creating operational tasks.

## Getting Started

### Prerequisites

- Python 3.10+
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

### 4. Configure Environment Variables

Create a `.env` file in the project root.

Example configuration:

```env
DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/enterprise_ai

JWT_SECRET_KEY=your_generated_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Never commit your actual `.env` file, passwords or signing keys to version control.

### 5. Start the Application

The application setup and database migration instructions are being updated as the RevOps schema transition is implemented.

Once the database schema is synchronized with the current application models, start the development server using:

```bash
fastapi dev app/main.py
```

### 6. API Documentation

Once the application is running:

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

## Engineering Principles

The project follows these development principles:

- Modular and maintainable application architecture.
- Separation of API, service, schema and data-access layers.
- Relational database integrity and controlled transactions.
- Secure authentication and authorization.
- Automated unit and integration testing.
- Evidence-based AI responses.
- Controlled agent tool execution.
- Human approval for consequential business actions.
- AI evaluation, observability and reliability.
- Secure credential and sensitive-data management.

## Project Roadmap

The long-term development objective is to deliver a deployable enterprise AI application with:

1. A relational B2B Revenue Operations database.
2. Reliable business analytics services.
3. LLM-powered natural-language interaction.
4. RAG-based enterprise knowledge retrieval.
5. Stateful LangGraph agent workflows.
6. MCP-based business tool integration.
7. Permission-controlled operational actions.
8. Automated AI evaluation and monitoring.
9. Docker-based deployment on AWS.

## Repository Status

**Project:** Enterprise Revenue Operations AI Agent  
**Domain:** Applied AI, Agentic AI and Enterprise Automation  
**Development:** 60-day practical engineering roadmap  
**Current Stage:** RevOps database modelling and backend engineering  
**Status:** In active development

---

The objective is to build a working enterprise AI system that can retrieve business information, analyse revenue performance, reason through multi-step workflows and execute controlled operational actions.

