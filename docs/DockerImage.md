# ExaFS Docker Installation

This guide explains how to create a Docker runtime image for ExaFS using the `jirivrany/exafs-base` base image.

## Prerequisites

- Docker installed on your system
- A running database instance 
- ExaBGP service configured and running (see ExaBGP Setup section)
- Network connectivity between containers/services

> **Note:** This guide focuses only on building the ExaFS Docker container. Database, ExaBGP, and other services are not included and must be set up separately.
> There is full stack deployment Ansible playbook in separate repository  [ExaFS Ansible Deploy](https://github.com/CESNET/ExaFS-deploy)

## Quick Start

### 1. Create Project Structure

Create a directory for your ExaFS Docker setup:

```bash
mkdir exafs-docker
cd exafs-docker
```

### 2. Create Dockerfile

Create a `Dockerfile` with the following content:

```dockerfile
# Use the ExaFS base image
FROM jirivrany/exafs-base:latest

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV USER_ID=1000
ENV GROUP_ID=1000
ENV USER_NAME=deploy
ENV GROUP_NAME=deploy
ENV FLASK_APP=run.py
ENV TZ="Europe/Prague"

# Create a group and user 
RUN addgroup -g $GROUP_ID $GROUP_NAME && \
    adduser --shell /sbin/nologin --disabled-password \
    --uid $USER_ID --ingroup $GROUP_NAME $USER_NAME

# Create logs directory and set ownership BEFORE switching to deploy user
RUN mkdir -p /app/logs && chown -R $USER_NAME:$GROUP_NAME /app

# Copy application files
COPY --chown=$USER_NAME:$GROUP_NAME ./run.py /app/run.py
COPY --chown=$USER_NAME:$GROUP_NAME ./config.py /app/config.py

# Optional: Copy instance configuration override if needed
# COPY --chown=$USER_NAME:$GROUP_NAME ./instance_config_override.py /app/instance_config_override.py

# Change to the deploy user
USER $USER_NAME

# Set the working directory
WORKDIR /app

# Add user bin to PATH
ENV PATH="/home/${USER_NAME}/.local/bin:${PATH}"

# Expose the application port
EXPOSE 8000

# Command to run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "run:app"]
```

### 3. Create Required Files


#### run.py

Create a `run.py` file as the application entry point. Start from `run.example.py` in the repository and make customizations if needed.

#### config.py

Create a `config.py` file with your ExaFS configuration. Start from `config.example.py` in the repository and make customizations if needed. 

# You may need to add other configuration options, such as:
# - Database connection settings (host, port, user, password)
# - Logging configuration
# - Secret keys and API tokens (use environment variables for sensitive data)
# - Integration settings for external services (e.g., ExaBGP, monitoring)
# For a full list of available options, see the ExaFS documentation or config.example.py in the repository.
```

> **Important:** Always use environment variables for sensitive data like database passwords and secret keys.

### 4. Build the Docker Image

Build your ExaFS runtime image:

```bash
docker build -t exafs:latest .
```

To build a specific version:

```bash
docker build -t exafs:1.1.6 .
```

### 5. Run the Container

Run the container with environment variables:

```bash
docker run -d \
  --name exafs \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:password@db-host:5432/exafs" \
  -e SECRET_KEY="your-secret-key" \
  -e EXABGP_HOST="exabgp-host" \
  -e EXABGP_PORT="5000" \
  -v /path/to/logs:/app/logs \
  exafs:latest
```

## Configuration Options

### Environment Variables

You can customize the container using these environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `SECRET_KEY` | Flask secret key for sessions | - |
| `EXABGP_HOST` | ExaBGP service hostname | `exabgp` |
| `EXABGP_PORT` | ExaBGP service port | `5000` |
| `TZ` | Timezone | `Europe/Prague` |
| `FLASK_APP` | Flask application entry point | `run.py` |

### Custom User and Group IDs

If you need to match host user/group IDs, modify the Dockerfile:

```dockerfile
ENV USER_ID=1001
ENV GROUP_ID=1001
```

### Instance Configuration Override

For advanced customization, you can use `instance_config_override.py`:

1. Uncomment the COPY line in the Dockerfile
2. Create `instance_config_override.py` with your custom settings
3. Rebuild the image

## Volume Mounts

Consider mounting these directories:

```bash
docker run -d \
  --name exafs \
  -p 8000:8000 \
  -v /path/to/logs:/app/logs \
  -v /path/to/config.py:/app/config.py:ro \
  exafs:latest
```

## Further Reading

- [ExaFS Ansible Deploy](https://github.com/CESNET/ExaFS-deploy) - Full deployment with Docker Compose
- [ExaFS Installation Guide](./INSTALL.md) - General installation instructions
- [Database Migrations](./DB_MIGRATIONS.md) - Database schema updates