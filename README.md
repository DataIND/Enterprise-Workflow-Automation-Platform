# Enterprise Workflow Automation Platform

A scalable event-driven workflow automation backend platform built using FastAPI, RabbitMQ, Celery, Redis, PostgreSQL, and Docker.

---

# Project Overview

The Enterprise Workflow Automation Platform enables organizations to create automated workflows triggered by system events.

The platform supports:

* Workflow automation
* Event-driven architecture
* Distributed background processing
* Retry & DLQ mechanisms
* Real-time notifications
* Multi-tenant organizations
* Async task execution
* WebSocket updates

Inspired by systems like:

* Zapier
* n8n
* Apache Airflow
* Temporal

---

# Tech Stack

| Component          | Technology           |
| ------------------ | -------------------- |
| API Framework      | FastAPI              |
| Database           | PostgreSQL           |
| ORM                | SQLAlchemy 2.0 Async |
| Queue Broker       | RabbitMQ             |
| Background Workers | Celery               |
| Cache              | Redis                |
| Authentication     | JWT                  |
| Realtime           | WebSockets           |
| Reverse Proxy      | Nginx                |
| Monitoring         | Prometheus + Grafana |
| Containerization   | Docker               |

---

# Features

## Authentication & Security

* JWT Authentication
* Refresh Tokens
* Password Hashing
* Role-Based Access Control (RBAC)
* Request Validation
* Rate Limiting

---

## Workflow Management

* Create workflows
* Update workflows
* Enable/Disable workflows
* Trigger-based automation
* Execution history tracking

---

## Event-Driven Processing

* RabbitMQ event bus
* Distributed workers
* Asynchronous execution
* Workflow orchestration

---

## Background Processing

Celery workers handle:

* Email sending
* Webhook execution
* Notifications
* Retry processing
* Cleanup jobs

---

## Real-Time Communication

* WebSocket notifications
* Live workflow execution updates
* Redis Pub/Sub integration

---

## Reliability Features

* Automatic retries
* Exponential backoff
* Dead Letter Queue (DLQ)
* Idempotent task execution

---

# High-Level Architecture

```text
Client
   ↓
Nginx
   ↓
FastAPI Application
   ↓
Workflow Engine
   ↓
RabbitMQ Event Bus
   ↓
Celery Workers

Redis:
- caching
- websocket pub/sub
- rate limiting

PostgreSQL:
- users
- workflows
- executions
- audit logs
```

---

# Project Structure

```text
enterprise-workflow-platform/
│
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   ├── workers/
│   ├── websocket/
│   ├── integrations/
│   ├── middleware/
│   ├── utils/
│   ├── tests/
│   └── main.py
│
├── docker/
├── alembic/
├── .env
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# Core Modules

## Authentication Module

APIs:

```http
POST /auth/register
POST /auth/login
POST /auth/refresh
GET /auth/me
```

Features:

* JWT Authentication
* Refresh tokens
* Secure password hashing

---

## Organization Module

Features:

* Multi-tenant organizations
* Team management
* RBAC permissions

Roles:

* Owner
* Admin
* Member

---

## Workflow Module

Features:

* Workflow CRUD
* Trigger management
* Action execution
* Condition validation

---

## Event Engine

Responsibilities:

* Receive events
* Publish to RabbitMQ
* Trigger workflows
* Route jobs to workers

---

## Workflow Execution Engine

Responsibilities:

* Execute workflow actions
* Manage retries
* Handle failures
* Track execution state

---

## Notification Module

Supports:

* Email notifications
* WebSocket notifications
* Retry alerts
* Execution alerts

---

# Example Workflow

## Example 1

WHEN:

* payment fails

THEN:

* send email
* retry payment
* notify admin
* create support ticket

---

## Example 2

WHEN:

* user registers

THEN:

* send welcome email
* notify Slack
* create onboarding task

---

# Database Tables

## users

* id
* email
* password_hash
* created_at

---

## organizations

* id
* name
* owner_id

---

## workflows

* id
* organization_id
* name
* trigger_type
* is_active

---

## workflow_executions

* workflow_id
* status
* started_at
* completed_at

---

## audit_logs

* user_id
* action
* entity_type
* created_at

---

# Redis Usage

Redis is used for:

* Caching
* Rate limiting
* WebSocket Pub/Sub
* Distributed locks
* Temporary execution state

---

# RabbitMQ Queues

```text
event_queue
email_queue
retry_queue
webhook_queue
dead_letter_queue
```

---

# Celery Tasks

```text
send_email
retry_workflow
send_webhook
generate_reports
cleanup_logs
```

---

# Setup Instructions

## 1. Clone Repository

```bash
git clone https://github.com/your-username/workflow-platform.git
```

---

## 2. Navigate To Project

```bash
cd workflow-platform
```

---

## 3. Create Environment File

Create `.env` file:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/workflow_db

JWT_SECRET_KEY=SUPER_SECRET_KEY
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

REDIS_URL=redis://redis:6379/0

CELERY_BROKER_URL=pyamqp://guest:guest@rabbitmq//
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

---

## 4. Build & Start Containers

```bash
docker-compose up --build
```

---

## 5. Run Database Migrations

```bash
alembic upgrade head
```

---

## 6. Open Swagger Documentation

```text
http://localhost:8000/docs
```

---

# API Endpoints

## Authentication APIs

```http
POST /auth/register
POST /auth/login
POST /auth/refresh
GET /auth/me
```

---

## Organization APIs

```http
POST /organizations
GET /organizations
POST /organizations/{id}/invite
```

---

## Workflow APIs

```http
POST /workflows
GET /workflows
GET /workflows/{id}
PATCH /workflows/{id}
DELETE /workflows/{id}
```

---

## Event APIs

```http
POST /events/publish
```

---

## Execution APIs

```http
GET /executions
GET /executions/{id}
```

---

# WebSocket Endpoints

```text
/ws/executions
/ws/notifications
```

---

# Monitoring & Observability

## Metrics

* API latency
* Workflow success rate
* Queue latency
* Worker health
* Retry counts
* Failed executions

---

## Tools

* Prometheus
* Grafana

---

# Testing

## Run Tests

```bash
pytest
```

---

## Test Types

* Unit Tests
* API Tests
* Integration Tests
* Worker Tests

---

# Deployment Architecture

## AWS Deployment

Services Used:

* EC2
* Docker Compose
* Nginx
* CloudWatch Logs

---

# Scalability Features

* Async APIs
* Distributed workers
* Queue-based processing
* Horizontal scaling
* Redis caching
* Non-blocking I/O

---

# Reliability Features

* Retry mechanisms
* Dead Letter Queue
* Idempotent execution
* Failure recovery

---

# Advanced Concepts Demonstrated

* Distributed Systems
* Event-Driven Architecture
* Async Programming
* Background Processing
* Scalability Engineering
* Reliability Engineering
* Fault-Tolerant Systems
* Real-Time Communication

---

# Development Roadmap

## Phase 1

* FastAPI setup
* PostgreSQL
* JWT Authentication
* Docker setup

---

## Phase 2

* Organizations
* RBAC
* Workflow CRUD

---

## Phase 3

* RabbitMQ integration
* Celery workers
* Event publishing

---

## Phase 4

* Retry system
* DLQ
* Execution tracking

---

## Phase 5

* WebSockets
* Notifications
* Real-time updates

---

## Phase 6

* Monitoring
* Metrics
* Logging

---

## Phase 7

* Testing
* CI/CD
* AWS deployment

---

# Resume Project Description

Designed and developed a scalable event-driven workflow automation backend using FastAPI, PostgreSQL, Redis, RabbitMQ, Celery, Docker, and WebSockets supporting distributed task execution, workflow orchestration, retry mechanisms, real-time notifications, RBAC, async APIs, and fault-tolerant background processing.

---

# Skills Demonstrated

* FastAPI
* Async Python
* PostgreSQL
* Redis
* RabbitMQ
* Celery
* Docker
* JWT
* WebSockets
* Distributed Systems
* Event-Driven Architecture
* Scalability Engineering
* System Design
* Reliability Engineering

---

# Future Enhancements

* Workflow visual builder
* Kafka integration
* Kubernetes deployment
* Saga Pattern
* Event Sourcing
* CQRS Architecture
* Distributed tracing
* OAuth integrations
* Multi-region deployment

---

# Author

Akash Jadhav
