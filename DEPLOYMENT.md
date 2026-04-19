# Learn Your Way - Docker Deployment Guide

This guide explains how to deploy the Learn Your Way application using Docker containers.

## Prerequisites

### Software Required
- **Docker** (version 20.10 or higher)
- **Docker Compose** (version 1.29 or higher)
- **Git** (to clone the repository)

### Installation Commands
```bash
# Install Docker on Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Log out and log back in to apply Docker group changes
```

## Quick Start

### 1. Clone the Repository
```bash
git clone <your-repository-url> lear_your_way
cd lear_your_way
```

### 2. Configure Environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit the environment file with your settings
nano .env
```

### 3. Deploy the Application
```bash
# Make the deploy script executable
chmod +x deploy.sh

# Run the deployment script
./deploy.sh
```

## Manual Deployment Steps

If you prefer to deploy manually:

### 1. Build and Start Services
```bash
# Build all Docker images
docker-compose build

# Start all services in detached mode
docker-compose up -d

# View running services
docker-compose ps
```

### 2. Verify Deployment
```bash
# Check service logs
docker-compose logs -f

# Test health endpoint
curl http://localhost:8000/health

# Access frontend in browser
open http://localhost:3000
```

## Configuration Options

### Environment Variables (.env file)
```bash
# Security
SECRET_KEY=your-super-secret-key-change-this-in-production

# AI Service API Keys (Optional)
# OPENAI_API_KEY=your-openai-api-key-here
# GOOGLE_API_KEY=your-google-ai-key-here

# Custom Domain (Optional)
# DOMAIN=your-domain.com
# EMAIL=admin@your-domain.com
```

### Service Ports
- **Frontend**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **PostgreSQL**: `localhost:5432` (for development/debugging)
- **Nginx Proxy** (optional): `http://localhost:8927`

## Production Deployment

### With Custom Domain and HTTPS

1. **Update .env file:**
```bash
DOMAIN=your-domain.com
EMAIL=admin@your-domain.com
```

2. **Enable nginx proxy:**
```bash
docker-compose --profile production up -d
```

3. **Set up SSL certificate:**
```bash
# Using Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Data Persistence

The application uses persistent volumes for:
- **Database**: PostgreSQL data (production-grade)
- **Uploads**: PDF files and processed content
- **SSL certificates**: (if using HTTPS)

### Database Management

Use the provided database management script:

```bash
# Make it executable
chmod +x db-manage.sh

# Check database status
./db-manage.sh status

# Open PostgreSQL shell
./db-manage.sh shell

# Create backup
./db-manage.sh backup

# Restore from backup
./db-manage.sh restore backup_file.sql

# Reset database (WARNING: deletes all data)
./db-manage.sh reset

# Show database logs
./db-manage.sh logs
```

## Service Management

### Common Commands
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Rebuild specific service
docker-compose up -d --build backend

# Scale services (if needed)
docker-compose up -d --scale backend=2
```

### Database Management (Legacy SQLite)
If you're still using SQLite (not recommended for production):

```bash
# Access database container
docker-compose exec backend bash

# Backup SQLite database
docker-compose exec backend cp learn_your_way.db /backup/

# Restore SQLite database
docker cp backup.db lear_your_way_backend_1:/app/learn_your_way.db
```

### PostgreSQL Database Management
For PostgreSQL (recommended for production):

```bash
# Access PostgreSQL container
docker-compose exec postgres psql -U postgres -d lear_your_way

# Or use the management script
./db-manage.sh status
./db-manage.sh shell
```

## Monitoring and Troubleshooting

### Health Checks
```bash
# Check service health
docker-compose ps

# Test API health
curl http://localhost:8000/health

# Check nginx status
curl http://localhost/health
```

### Common Issues

1. **Port conflicts:**
   - Make sure ports 3000, 8000, and 80 are not in use
   - Modify ports in docker-compose.yml if needed

2. **Permission issues:**
   - Ensure Docker daemon is running
   - Check user has Docker permissions

3. **Build failures:**
   - Clear Docker cache: `docker system prune -a`
   - Rebuild: `docker-compose build --no-cache`

4. **Service not responding:**
   - Check logs: `docker-compose logs <service-name>`
   - Verify network connectivity
   - Check resource usage

## Security Considerations

1. **Change default secrets:**
   - Update `SECRET_KEY` in .env file
   - Use strong, unique passwords

2. **Network security:**
   - Use HTTPS in production
   - Configure firewall rules
   - Limit API access if needed

3. **File uploads:**
   - Validate file types and sizes
   - Scan for malware
   - Use secure file storage

## Scaling Options

### Horizontal Scaling
```bash
# Scale backend services
docker-compose up -d --scale backend=3

# Add load balancer configuration in nginx
```

### Vertical Scaling
- Modify resource limits in docker-compose.yml
- Add memory and CPU constraints
- Monitor resource usage

## Backup and Recovery

### Automated Backup Script
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec backend cp learn_your_way.db /backup/backup_$DATE.db
```

### Restore from Backup
```bash
docker cp backup.db lear_your_way_backend_1:/app/learn_your_way.db
docker-compose restart backend
```

## Support

For deployment issues:
1. Check the logs: `docker-compose logs`
2. Verify configuration files
3. Test individual services
4. Check system resources