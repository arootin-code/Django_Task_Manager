# Celery + Django REST Framework + Redis + smtp4dev + PostgreSQL + Task Manager

A practical project demonstrating **Async Task Processing** architecture in Django, extended into a real **Task Manager** application.

In this project a real scenario is implemented:

The user registers through the API, Django responds quickly, then the welcome email is sent in the background by a **Celery Worker** without keeping the user waiting.

A scheduled Celery Beat task also sends reminder emails for tasks that remain pending for more than 24 hours.

The following real production tools are used:

* Django REST Framework for building the API
* Nginx as Reverse Proxy
* Gunicorn for running Django in production
* PostgreSQL for data storage
* Redis as Message Broker
* Celery for background tasks
* Celery Beat for scheduled tasks
* smtp4dev for email simulation
* Flower for Celery monitoring
* Locust for load testing
* SimpleJWT for JWT authentication
* Bootstrap (local) for the web UI

---

# Project Goal

The goal of this project is to teach the full lifecycle of an async request in Django:
User Request
|
▼
Django API
|
├── Save data to PostgreSQL
|
└── Send Task to Redis
|
▼
Celery Worker
|
▼
Send Email
|
▼
smtp4dev

```

The user should not wait for heavy operations like sending email.

Django only creates the Task and the Worker does the work in the background.

---

# System Architecture
Browser / curl / Locust

|
▼

Nginx :80

|
▼

Gunicorn

|
▼

Django REST Framework

      /    \

      /    \

      ▼     ▼

PostgreSQL Redis

Users + TaskResult Message Broker

|
▼

Celery Worker

|
▼

smtp4dev

▲

|

Celery Beat

|

Periodic Tasks

Flower :5555

Celery Monitoring

```

---

# Full Request Flow

## 1. User Registration

The user sends:
POST /register/

```

Example:

```json
{
 "username": "Jamall",
 "email": "devops523@gmail.com",
 "password": "12345678"
}
2. Django Processes the Request
```
Django:

Validates the input

Saves the User in PostgreSQL

Creates a Celery Task

Example:

```
send_welcome_email()
3. Task Sent to Redis
Redis acts as a message queue:

```
Redis Queue

[
   send_welcome_email(task_id=123)
]
4. Celery Worker Receives the Task
Worker:

```
Receive Task
        |
Execute Business Logic
        |
Send Email
5. Email Sending
For development, smtp4dev is used.

No real email is sent. Instead it is shown in the Web UI at:

```
http://localhost:5000
6. Task Result Storage
The task result is saved in PostgreSQL:

```
TaskResult
status = SUCCESS
This information is visible through:

API

Flower

Monitoring system

Original Features (before my changes)
The base project already provided:

POST /register/ - creates a user and dispatches a welcome email asynchronously

GET /tasks/<task_id>/ - polls a Celery task's status (backed by django-db result backend)

send_welcome_email Celery task with retry + exponential backoff

cleanup_old_task_results periodic task (Celery Beat)

Docker Compose stack with Nginx, Gunicorn, PostgreSQL, Redis, Flower, smtp4dev

Four New Features
Feature 1 - Task CRUD with per-user isolation
Goal: allow authenticated users to create, list, update, and delete their own tasks.

Model: jobs.models.Task (title, description, status, created_at, finished_at, reminder_sent, user FK).

Endpoints:

GET/POST /api/tasks/

GET/PUT/PATCH/DELETE /api/tasks/{id}/

Access control: get_queryset() filters by request.user; perform_create() sets user=request.user. A user can never see or modify another user's tasks.

Tests: TaskCRUDTests (3 tests).

Feature 2 - JWT Authentication
Goal: stateless authentication for the API.

Endpoints:

POST /api/auth/login/ - returns access and refresh tokens

POST /api/auth/refresh/ - returns a new access token

Default permission: IsAuthenticated (set globally in settings.REST_FRAMEWORK).

Tests: JWTAuthTests (3 tests), including a check that unauthenticated requests return 401.

Feature 3 - Async Email Notifications on Complete / Fail
Goal: notify the user asynchronously when a task is completed or failed.

Endpoints:

POST /api/tasks/{id}/complete/ - sets status=SUCCESS, finished_at=now(), dispatches send_success_email.delay(...)

POST /api/tasks/{id}/fail/ - sets status=FAILED, dispatches send_failure_email.delay(...)

Celery tasks: jobs.tasks.send_success_email, jobs.tasks.send_failure_email (retry + exponential backoff, same pattern as the base project's send_welcome_email).

Tests: CeleryEmailTests (3 tests) using unittest.mock.patch on .delay to verify dispatch without hitting SMTP.

Feature 4 - 24-Hour Reminder via Celery Beat
Goal: automatically remind users of tasks that have been pending for more than 24 hours.

Task: jobs.tasks.send_reminder_for_stale_tasks - queries Task.objects.filter(status=PENDING, reminder_sent=False, created_at__lt=now-24h) and sends one email per task, then sets reminder_sent=True.

Scheduling: CELERY_BEAT_SCHEDULE runs it every 60 seconds (production value would be 3600).

Optimization: select_related("user") avoids N+1 queries.

Tests: ReminderTests (3 tests) - covers the happy path, the "too new" case, and the "already reminded" case.

Project Services
Service	Responsibility
Django	Build API and handle requests
Nginx	Reverse Proxy
Gunicorn	Run Django workers
PostgreSQL	Main Database
Redis	Message Broker
Celery Worker	Run async tasks
Celery Beat	Run scheduled tasks
smtp4dev	Email testing
Flower	Celery monitoring
Locust	API load testing
Running the Project
First, create the environment file:

bash
cp .env.example .env
Then:

bash
docker compose up --build
Check status:

bash
docker compose ps
All services should be Running.

Service URLs
Service	URL
Django API	http://localhost
smtp4dev	http://localhost:5000
Flower	http://localhost:5555/flower/
Locust	http://localhost:8089
Manual Testing
Register a user:

bash
curl -X POST http://localhost/register/ \
-H "Content-Type: application/json" \
-d '
{
"username":"Bahram",
"email":"devops523@gmail.com",
"password":"12345678"
}
'
The response includes a Task ID.

Example:

json
{
"user":"ali",
"task_id":"xxxxxxxx"
}
Check Task status:

bash
curl http://localhost/tasks/<task_id>/
Result before execution:

```
PENDING
After success:

```
SUCCESS
Viewing Emails
Open:

```
http://localhost:5000
You will see the Welcome email.

Viewing Tasks with Flower
Open:

```
http://localhost:5555/flower/
In Flower you can see:

Workers

Executed tasks

Successful tasks

Failed tasks

Queues

Celery Beat
This project has a scheduled task:

```
cleanup_old_task_results
which runs every 60 seconds.

View logs:

bash
docker compose logs -f celery-beat celery-worker
Load Testing with Locust
Open:

```
http://localhost:8089
Configure:

```
Users: 100
Spawn Rate: 10
Locust sends registration requests and tests the full path:

```
Request
  ↓
Django
  ↓
PostgreSQL
  ↓
Redis
  ↓
Celery
  ↓
Email
Project Structure
```
django-celery-async-architecture-demo/
├── src/
│   ├── manage.py
│   ├── config/
│   │   ├── settings.py
│   │   ├── celery.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── notifications/
│   │   ├── tasks.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── urls.py
│   └── jobs/                 # NEW: Task Manager app
│       ├── models.py
│       ├── serializers.py
│       ├── views.py
│       ├── views_web.py
│       ├── urls.py
│       ├── tasks.py
│       ├── admin.py
│       ├── tests.py          # 12 automated tests
│       ├── migrations/
│       ├── static/jobs/      # Bootstrap, CSS, JS
│       └── templates/jobs/   # HTML pages
├── docker/
│   ├── django/
│   └── nginx/
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
├── locustfile.py
├── .env.example
└── README.md
Running the Tests
bash
docker compose exec django python manage.py test jobs -v 2
Expected output: Ran 12 tests ... OK.

The tests use unittest.mock.patch for all outgoing email, so they do not require smtp4dev, Redis, or Celery workers to be running.

API Documentation
Method	Path	Auth	Description
POST	/api/auth/login/	No	Obtain access + refresh
POST	/api/auth/refresh/	No	Refresh access
GET/POST	/api/tasks/	Yes	List / create tasks
GET/PUT/PATCH/DELETE	/api/tasks/{id}/	Yes	Retrieve / update / delete a task
POST	/api/tasks/{id}/complete/	Yes	Mark task as SUCCESS
POST	/api/tasks/{id}/fail/	Yes	Mark task as FAILED
All authenticated endpoints expect Authorization: Bearer <access>.

Web UI: /login/, /sign_up/, /tasks-ui/, /tasks-ui/new/.

Sample Output
After POST /api/tasks/{id}/complete/, the response looks like:

json
{
  "id": 3,
  "title": "Email test task",
  "description": "Should send real email",
  "status": "SUCCESS",
  "created_at": "2026-11-13T11:35:44Z",
  "finished_at": "2026-11-13T11:36:04Z"
}
The reminder task logs:

```
Sent reminder emails for 1 stale tasks
Task jobs.tasks.send_reminder_for_stale_tasks[...] succeeded: 'sent 1 reminder emails'
Educational Concepts
By studying this project you will learn:

Django
Django REST Framework

API Design

Database Integration

Custom Model Methods

Migration Management

Celery
Async Task

Worker

Broker

Result Backend

Beat Scheduler

bind=True, autoretry_for, retry with exponential backoff

Redis
Message Queue

Task Distribution

Authentication
SimpleJWT

Access / Refresh tokens

IsAuthenticated permission

Object-level permission (get_queryset filtering)

Production Deployment
Nginx Reverse Proxy

Gunicorn

Docker Compose

Monitoring
Flower

Task Tracking

Testing
Django APITestCase

unittest.mock.patch for external services

Locust Load Testing

Automated tests (12)

Optimization
select_related to avoid N+1 queries

Production Notes
This is an educational project.

For real production the following should be added:

HTTPS with SSL

Secrets Management

Rate Limiting

Prometheus + Grafana

Central Logging

Kubernetes Deployment

AI Usage Disclosure
Parts of this project were developed with the assistance of an AI coding assistant (Claude). The AI was used for:

Drafting the initial Task model and DRF ViewSet structure

Suggesting the 12 test cases and their mock strategy

Reviewing the JWT configuration and Bootstrap layout

All AI-generated code was read, understood, tested locally (via python manage.py test and manual API calls), and adapted to the project. The author is responsible for every line of code submitted.

Original Author
Jamall (Bahram) Mahmoudi
devops523@gmail.com

Created for learning and demonstrating:
Django + Celery + Redis + Docker Production Architecture

Extended By
This project was extended by a student as the final project of the Backend Development with Django course, adding:

Task Manager domain model

JWT authentication

Async email notifications on task completion/failure

24-hour reminder via Celery Beat

Bootstrap web UI

12 automated tests

If you found this project useful
Give it a Star on GitHub