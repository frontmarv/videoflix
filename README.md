# Videoflix - Backend API

A Django REST Framework backend application for video hosting and streaming with HLS (HTTP Live Streaming) support. The application provides user authentication, video management, and adaptive multi-resolution video delivery.

## Features

- **User Authentication**: Email-based authentication with JWT tokens stored in HTTP-only cookies
- **Account Activation**: Email-based account activation workflow
- **Video Management**: Upload and manage videos with automatic processing
- **Multi-Resolution Delivery**: Automatic conversion to 480p, 720p, and 1080p
- **HLS Streaming**: HTTP Live Streaming support for adaptive bitrate streaming
- **Admin Interface**: Full Django admin interface for managing users and videos
- **Docker Support**: Complete containerization with Docker Compose

## Technology Stack

- **Backend Framework**: Django 6.0+ with Django REST Framework
- **Authentication**: JWT (JSON Web Tokens) with SimplJWT
- **Database**: PostgreSQL
- **Task Queue**: Redis with Django-RQ
- **Video Processing**: FFmpeg
- **Containerization**: Docker & Docker Compose
- **Email Service**: SMTP-based email delivery

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 1.29 or higher
- **Git**: For cloning the repository
- **A text editor or IDE**: For configuration

**Note**: You do NOT need Python, PostgreSQL, Redis, or FFmpeg installed locally. All dependencies are handled by Docker.

## Project Structure

```
videoflix/
├── authentication_app/          # User authentication module
│   ├── api/
│   │   ├── views.py            # Authentication endpoints
│   │   ├── serializers.py       # Request/response serializers
│   │   ├── urls.py              # URL routing
│   │   └── utils.py             # Helper functions
│   ├── models.py                # CustomUser model
│   ├── managers.py              # Custom user manager
│   ├── tokens.py                # Token generators
│   └── tasks.py                 # Celery/RQ tasks
├── videos_app/                  # Video management module
│   ├── api/
│   │   ├── views.py            # Video endpoints
│   │   ├── serializers.py       # Video serializers
│   │   └── urls.py              # URL routing
│   ├── models.py                # Video and VideoResolution models
│   ├── signals.py               # Signal handlers
│   └── tasks.py                 # Video processing tasks
├── core/                        # Project configuration
│   ├── settings.py              # Django settings
│   ├── urls.py                  # Main URL configuration
│   ├── wsgi.py                  # WSGI application
│   └── task_service.py          # Task orchestration
├── docker-compose.yml           # Multi-container setup
├── backend.Dockerfile           # Backend container image
├── manage.py                    # Django management script
└── requirements.txt             # Python dependencies
```

## Quick Start with Docker

### 1. Clone the Repository

```bash
git clone <repository-url>
cd videoflix
```

### 2. Set Up Environment Variables

The easiest way is to copy the template file and customize it with your values:

**On Windows (PowerShell):**
```bash
Copy-Item .env.template .env
```

**On macOS/Linux:**
```bash
cp .env.template .env
```

Then edit the `.env` file with your favorite text editor:

```env
# Django Configuration (REQUIRED - Change these values!)
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=your_secure_password  # ← Change this to a strong password
DJANGO_SUPERUSER_EMAIL=admin@example.com        # ← Change this to your admin email
SECRET_KEY=your-secret-key-here                 # ← Generate a random secret key (min 50 chars)
DEBUG=False                                      # Keep False in production
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com  # ← Add your domain here

# CORS and Security (OPTIONAL - Only change if not localhost)
CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://yourdomain.com
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://yourdomain.com

# Database Configuration (OPTIONAL - Good defaults for Docker)
DB_NAME=videoflix_db
DB_USER=videoflix_user
DB_PASSWORD=your_database_password              # ← Change this if you want
DB_HOST=db                                       # Keep as 'db' for Docker
DB_PORT=5432                                     # Standard PostgreSQL port

# JWT Configuration (OPTIONAL - Leave as is for development)
ACCESS_TOKEN_LIFETIME=60                         # Minutes until access token expires
REFRESH_TOKEN_LIFETIME=1440                      # Minutes until refresh token expires (1 day)
JWT_ALGORITHM=HS256

# Redis Configuration (OPTIONAL - Good defaults for Docker)
REDIS_HOST=redis
REDIS_LOCATION=redis://redis:6379/1
REDIS_PORT=6379
REDIS_DB=0

# Email Configuration (REQUIRED for production and to register an account, OPTIONAL for development)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com            # ← Change to your email
EMAIL_HOST_PASSWORD=your-app-password           # ← Use Gmail App Password (not your password!)
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=noreply@videoflix.com
```

**Quick Setup (Development):**
If you just want to test locally, only change these values:
- `DJANGO_SUPERUSER_PASSWORD` - Any password you want
- `DJANGO_SUPERUSER_EMAIL` - Any email address
- `SECRET_KEY` - Generate one: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`

The rest can stay as is for local development.

**For Production:**
Make sure to also set:
- `DEBUG=False`
- `SECRET_KEY` - A strong random key
- `ALLOWED_HOSTS` - Your actual domain
- Email settings - So users can receive activation links

### 3. Build and Start Services

Build the Docker images:

```bash
docker-compose build
```

Start all services (database, Redis, backend, worker):

```bash
docker-compose up -d
```

The API will be available at: `http://localhost:8000`

### 4. Initialize the Database

Run migrations:

```bash
docker-compose exec backend python manage.py migrate
```

Create superuser account (if not using `DJANGO_SUPERUSER_*` env vars):

```bash
docker-compose exec backend python manage.py createsuperuser
```

### 5. Access the Application

- **API**: http://localhost:8000/api/
- **Admin Panel**: http://localhost:8000/admin/

## API Endpoints

All endpoints are prefixed with `/api/`

### Authentication Endpoints

#### User Registration
- **POST** `/api/register/`
  - Description: Create a new user account with email and password

#### User Login
- **POST** `/api/login/`
  - Description: Authenticate user and receive JWT tokens via HTTP-only cookies

#### Activate Account
- **GET** `/api/activate/<uidb64>/<token>/`
  - Description: Activate user account using email activation link

#### Password Reset Request
- **POST** `/api/password_reset/`
  - Description: Request password reset link sent to email address

#### Password Reset Confirm
- **GET** `/api/password_confirm/<uidb64>/<token>/`
  - Description: Validate password reset link
- **POST** `/api/password_confirm/<uidb64>/<token>/`
  - Description: Confirm password reset and set new password

#### User Logout
- **POST** `/api/logout/`
  - Description: Invalidate tokens and clear authentication cookies

#### Refresh Token
- **POST** `/api/token/refresh/`
  - Description: Generate new access token using refresh token from cookies

### Video Endpoints

#### List All Videos
- **GET** `/api/video/`
  - Description: Retrieve all videos (requires authentication)

#### HLS Playlist
- **GET** `/api/video/<video_id>/<resolution>/index.m3u8/`
  - Description: Get HLS master playlist for video streaming
  - Parameters: `video_id` (integer), `resolution` (480p, 720p, 1080p)

#### HLS Video Segment
- **GET** `/api/video/<video_id>/<resolution>/<segment_filename>`
  - Description: Get individual video segment (TS file) for streaming
  - Parameters: `video_id` (integer), `resolution` (480p, 720p, 1080p), `segment_filename` (e.g., segment_000.ts)


## Media Files

User-uploaded media is stored in the `/media/` volume:

- `/media/videos/original/` - Original uploaded videos
- `/media/videos/resolutions/` - Converted video resolutions
- `/media/thumbnails/` - Video thumbnails

## Video Processing

Videos are automatically processed after upload:

1. File gets uploaded to `/media/videos/original/`
2. Signal triggers video processing task
3. FFmpeg converts to 480p, 720p, 1080p
4. HLS playlist created for each resolution
5. `is_processed` flag set to True


## Email Configuration

The application sends emails for:

- Account activation links
- Password reset links

Configure SMTP settings in `.env`:

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password  # Gmail: Use App Password, not your main password
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=noreply@videoflix.com
```


