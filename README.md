# Craft-EG

Craft-EG is a robust and scalable e-commerce platform built with Django and Django REST Framework. It serves as a marketplace where artisans (suppliers) can showcase and sell their handcrafted products, and customers can browse, purchase, and review items. The platform also includes a comprehensive system for course enrollment, order management, payments, and real-time communication.

## Features
- **User Management:** Multi-role user system for customers, suppliers, and delivery personnel.
- **Authentication:** Secure, token-based authentication using JWT (`Simple JWT`) with email verification and password reset functionality.
- **Product Catalog:** Suppliers can manage products, categories, and collections.
- **Order & Cart Management:** A full-featured shopping cart, wishlist, and order processing system.
- **Payment Integration:** Seamless integration with Stripe for secure credit card payments.
- **Real-time Notifications:** WebSocket-based notifications for real-time updates using Django Channels.
- **Supplier & Delivery Profiles:** Dedicated profiles for suppliers and delivery personnel to manage their operations.
- **API Documentation:** Interactive API documentation is automatically generated using `drf-yasg` and is available at `/docs/`.

---

## Technology Stack
- **Backend:** Python, Django, Django REST Framework
- **Database:** PostgreSQL (recommended for production) or SQLite (for development)
- **Asynchronous Tasks:** `daphne`, `channels_redis`
- **Environment Management:** `django-environ`
- **Payments:** `Stripe`
- **API Documentation:** `drf-yasg`

---

## Prerequisites
Before you begin, ensure you have the following installed:
- Python (3.9+)
- pip
- Git

---

## Installation
Follow these steps to get the development environment up and running.

1.  **Clone the repository:**
    ```sh
    git clone [https://github.com/Waleeddarwesh/Craft.git](https://github.com/Waleeddarwesh/Craft.git)
    cd Craft
    ```
2.  **Set Up a Virtual Environment:**
    Create and activate a virtual environment:
    ```sh
    # On macOS and Linux
    python3 -m venv venv
    source venv/bin/activate
    
    # On Windows
    python -m venv venv
    venv\Scripts\activate
    ```
3.  **Navigate to the project directory:**
    ```sh
    cd Handcrafts
    ```

4.  **Install the required dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

5.  **Create a `.env` file:**
    Copy the contents of the `env.example` file and fill in the required values. This file should be placed in the project root.

    ```ini
    # .env
    SECRET_KEY=your-secret-key-here
    ENVIRONMENT=development
    DEBUG=True
    ALLOWED_HOSTS=127.0.0.1,localhost
    STRIPE_SECRET_KEY=your-stripe-secret-key-here
    DATABASE_URL=postgres://user:password@host:port/database_name
    REDIS_URL=redis://localhost:6379/0
    EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
    EMAIL_HOST=smtp.gmail.com
    EMAIL_HOST_USER=your-email@gmail.com
    EMAIL_HOST_PASSWORD=your-email-password-or-app-specific-password
    EMAIL_PORT=587
    CORS_ALLOWED_ORIGINS=http://localhost:3000,[http://127.0.0.1:3000](http://127.0.0.1:3000)
    CSRF_TRUSTED_ORIGINS=http://localhost:3000,[http://127.0.0.1:3000](http://127.0.0.1:3000)
    ```

6.  **Run database migrations:**
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

---

## Usage
Access the Swagger documentation to view all endpoints and their details:
- **Documentation**: [http://localhost:8000/docs/](http://localhost:8000/docs/)

---

## Contributing
We welcome contributions to the Craft application! If you would like to contribute, please follow these steps:

1.  Fork the repository.
2.  Create a new branch for your feature or bugfix:
    ```sh
    git checkout -b your-feature-branch
    ```
3.  Make your changes and commit them:
    ```sh
    git commit -m "Description of your changes"
    ```
4.  Push your changes to your fork:
    ```sh
    git push origin your-feature-branch
    ```
5.  Create a pull request with a detailed description of your changes.

---

## Contact
For any questions or inquiries, please contact:
- Name: [Waleed Darwesh]
- Email: [Waleeddarwesh2002@gmail.com]
