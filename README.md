# Craft-EG

Craft-EG is a comprehensive e-commerce platform built with Django and Django REST Framework, designed to serve as a dynamic marketplace for handcrafted products. The platform facilitates direct interaction between customers, artisans (crafters), and a dedicated delivery network, providing a seamless and secure experience for all user roles.

This project is a full-stack solution featuring over 150 well-documented API endpoints, ensuring robust data management and efficient communication across all services.

## Table of Contents
- [Features](#features)
- [Interfaces](#interfaces)
- [Technology Stack](#technology-stack)
- [Installation and Setup](#installation-and-setup)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [Contact](#contact)

---

## Features

- **Multi-Role User Management**: A flexible and secure user model supporting distinct roles for customers, crafters, and delivery personnel.
- **Secure Authentication**: Implements JSON Web Token (JWT) authentication using `Simple JWT`, complete with email verification and a robust password reset flow.
- **Dynamic E-commerce System**: A comprehensive suite of e-commerce functionalities, including product browsing, shopping carts, wishlists, and a streamlined order processing pipeline.
- **Course Management**: A dedicated module for crafters to create and publish courses, allowing customers to enroll and track their progress toward certification.
- **Real-time Chat and Notifications**: Utilizes Django Channels with Redis to provide real-time messaging between users and instant notifications for critical events, such as new orders or status updates.
- **Product and Collection Management**: Crafters can easily manage their product listings, organize items into themed collections, and track stock levels.
- **Order and Shipment Tracking**: A detailed order management system that handles complex shipment logistics, including multiple delivery stages and confirmation codes.

---

## Interfaces

The application is built with three distinct user interfaces, each optimized for its specific role:

- **Customer Interface**: A user-friendly front-end that allows customers to discover products, enroll in courses, manage their profiles, and communicate with crafters and delivery personnel.
- **Crafter Interface**: A powerful dashboard for artisans to manage their digital store. It provides tools for publishing and updating courses, managing product inventory, processing orders, and monitoring sales analytics.
- **Delivery Interface**: A streamlined, mobile-friendly interface for delivery personnel to receive shipment assignments, track delivery routes, and update order statuses in real time.

---

## Technology Stack

- **Backend**: Python 3.11, Django 5.0.3, Django REST Framework
- **Database**: PostgreSQL (recommended for production), SQLite (for local development)
- **Asynchronous Processing**: Daphne, Channels Redis
- **Security & Utilities**: `django-environ`, `drf-yasg`, `drf-simplejwt`, `corsheaders`
- **Deployment**: Docker, Docker Compose

---

## Installation and Setup

To set up the project locally, follow these steps.

1.  **Clone the repository:**
    ```sh
    git clone [https://github.com/Waleeddarwesh/Craft.git](https://github.com/Waleeddarwesh/Craft.git)
    cd Craft
    ```

2.  **Create and activate a virtual environment:**
    ```sh
    # On macOS and Linux
    python3 -m venv venv
    source venv/bin/activate
    
    # On Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Navigate to the project directory:**
    ```sh
    cd Handcrafts
    ```

4.  **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

5.  **Configure environment variables:**
    Create a `.env` file in the `Handcrafts` directory and add your configuration settings. A template is provided in `env.example`.

    ```ini
    # .env
    SECRET_KEY=your-secret-key-here
    ENVIRONMENT=development
    DEBUG=True
    ALLOWED_HOSTS=127.0.0.1,localhost
    DATABASE_URL=sqlite:///db.sqlite3
    REDIS_URL=redis://localhost:6379/0
    EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
    EMAIL_HOST=your-smtp-server.com
    EMAIL_PORT=587
    EMAIL_USE_TLS=True
    EMAIL_HOST_USER=your-email@example.com
    EMAIL_HOST_PASSWORD=your-email-password
    CORS_ALLOWED_ORIGINS=http://localhost:3000,[http://127.0.0.1:3000](http://127.0.0.1:3000)
    CSRF_TRUSTED_ORIGINS=http://localhost:3000,[http://127.0.0.1:3000](http://127.0.0.1:3000)
    ```

6.  **Run migrations:**
    ```sh
    python manage.py makemigrations
    python manage.py migrate
    ```

7.  **Create a superuser:**
    ```sh
    python manage.py createsuperuser
    ```

8.  **Start the development server:**
    ```sh
    python manage.py runserver
    ```
    The application will be available at `http://127.0.0.1:8000/`.

---

## API Documentation

The project uses `drf-yasg` to provide interactive API documentation. You can access the Swagger UI to explore all available endpoints:

- **Swagger UI**: [http://127.0.0.1:8000/swagger/](http://127.0.0.1:8000/swagger/)
- **ReDoc**: [http://127.0.0.1:8000/redoc/](http://127.0.0.1:8000/redoc/)

---

## Contributing

We welcome contributions to the Craft-EG project! To contribute, please follow these steps:

1.  Fork the repository.
2.  Create a new branch for your feature or bugfix:
    ```sh
    git checkout -b feature/your-feature-name
    ```
3.  Make your changes and commit them with a descriptive message:
    ```sh
    git commit -m "feat: Add new feature for user profiles"
    ```
4.  Push your changes to your forked repository:
    ```sh
    git push origin feature/your-feature-name
    ```
5.  Create a pull request to the `main` branch of the original repository.

---

## Contact

For any questions or inquiries, please contact:
- Name: Waleed Darwesh
- Email: Waleeddarwesh2002@gmail.com
