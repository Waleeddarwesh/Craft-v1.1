# 🧶 Craft Application - Version 1.1

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Django](https://img.shields.io/badge/Django-5.0-green)
![DRF](https://img.shields.io/badge/DRF-Rest_Framework-red)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

**Craft** is a comprehensive multi-vendor marketplace and e-learning platform designed to bridge the gap between handcraft suppliers (Crafters) and Customers.

This backend project integrates E-commerce logic, Social networking, Video streaming for courses, and Real-time communication into a scalable architecture.

---

# Table of Contents

- [Key Features](#key-features)
- [Technical Architecture](#technical-architecture)
- [User Interfaces](#user-interfaces)
- [Prerequisites](#prerequisites)
- [Installation - Docker Recommended](#installation---docker-recommended)
- [Installation - Manual](#installation---manual)
- [Environment Configuration](#environment-configuration)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [Contact](#contact)

---

# Key Features

## 🛒 E-commerce Core

- **Marketplace:** Multi-vendor support allowing Crafters to manage products and stock.
- **Order Management:** Complete order lifecycle management (Cart → Order → Shipment → Delivery).
- **Financial System:** Integrated Stripe payments, wallet system, and refund handling.
- **Promotions:** Coupon and discount management system.

## 🎓 E-Learning Platform

- **Courses:** Crafters can upload and manage educational video courses.
- **Progress Tracking:** Users can track course progress and enrollments.
- **Certificates:** Automatic certificate generation after course completion.

## 💬 Social & Real-Time Features

- **Real-Time Chat:** Messaging system using Django Channels and Redis.
- **Social Feed:** Follow system, likes, and activity feeds.
- **Notifications:** Real-time notifications for chats and order updates.

## 🤖 Smart Features

- **Recommendation System:** Product and course recommendations.
- **Background Tasks:** Celery integration for asynchronous processing.

---

# Technical Architecture

| Component | Technology |
|---|---|
| Backend Framework | Django & Django REST Framework |
| Database | PostgreSQL |
| Cache & Broker | Redis |
| Async Tasks | Celery |
| Real-Time Communication | Django Channels (ASGI) |
| Containerization | Docker & Docker Compose |
| Authentication | JWT (SimpleJWT) & Social Auth |
| API Documentation | Swagger (drf-yasg) |

---

# User Interfaces

The backend serves three separate frontend applications:

1. **Customer Application**
   - Browse products
   - Purchase courses
   - Social interaction

2. **Crafter Dashboard**
   - Product management
   - Course uploading
   - Sales analytics

3. **Delivery Application**
   - Shipment tracking
   - Delivery status updates

---

# Prerequisites

Before running the project, ensure the following are installed:

- Python 3.10+
- PostgreSQL
- Redis Server
- Git
- Docker & Docker Compose (Recommended)

---

# Installation - Docker Recommended

The easiest way to run the project is using Docker Compose.

## 1. Clone Repository

```bash
git clone https://github.com/Waleeddarwesh/Craft.git
cd Craft
```

## 2. Create Environment File

Create a `.env` file in the project root directory.

Example configuration is available in the Environment Configuration section below.

## 3. Build and Run Containers

```bash
docker-compose up --build
```

This command starts:

- Django Server
- PostgreSQL Database
- Redis Server
- Celery Workers

---

# Installation - Manual

## 1. Create Virtual Environment

### Linux / macOS

```bash
python -m venv venv
source venv/bin/activate
```

### Windows

```bash
venv\Scripts\activate
```

---

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 3. Configure Environment Variables

Create a `.env` file in the project root directory.

---

## 4. Apply Database Migrations

```bash
python manage.py migrate
```

---

## 5. Create Superuser

```bash
python manage.py createsuperuser
```

---

## 6. Run Development Server

```bash
python manage.py runserver
```

> Note: Redis must be running locally to use chat and background tasks.

---

# Environment Configuration

Create a `.env` file in the root directory (same level as `manage.py`).

```ini
# Core Settings
DEBUG=True
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL Database
DATABASE_URL=postgres://user:password@localhost:5432/craft_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Stripe Payments
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Google Authentication
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Email Configuration
EMAIL_HOST=sandbox.smtp.mailtrap.io
EMAIL_HOST_USER=your_user
EMAIL_HOST_PASSWORD=your_password
```

---

# API Documentation

After starting the server, API documentation will be available at:

## Swagger UI

```txt
http://localhost:8000/docs/
```

## ReDoc

```txt
http://localhost:8000/redoc/
```

---

# Contributing

1. Fork the repository

2. Create a feature branch

```bash
git checkout -b feature/AmazingFeature
```

3. Commit changes

```bash
git commit -m "Add AmazingFeature"
```

4. Push changes

```bash
git push origin feature/AmazingFeature
```

5. Open a Pull Request

---

# Contact

## Waleed Darwesh

Backend Software Engineer

📧 Email: Waleeddarwesh2002@gmail.com

🔗 LinkedIn:
https://www.linkedin.com/in/waleeddarwesh1/

🔗 GitHub:
https://github.com/Waleeddarwesh
