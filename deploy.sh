#!/bin/bash

# Learn Your Way Deployment Script
# This script deploys the application using Docker Compose

set -e

echo "🚀 Starting Learn Your Way deployment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Detect docker compose command (docker compose v2 or docker-compose v1)
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
    echo "✅ Using docker compose (V2)"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
    echo "✅ Using docker-compose (V1)"
else
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration before running the script again."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p backend/uploads
mkdir -p nginx/ssl

# Build and start services
echo "🔨 Building Docker images..."
$DOCKER_COMPOSE build

echo "🚀 Starting services..."
$DOCKER_COMPOSE up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
if $DOCKER_COMPOSE ps | grep -q "Up"; then
    echo "✅ Services are running successfully!"
    echo ""
    echo "🌐 Access your application at:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend API: http://localhost:8000"
    echo "   Health Check: http://localhost:8000/health"
    echo ""
    echo "📊 View logs with: $DOCKER_COMPOSE logs -f"
    echo "🛑 Stop services with: $DOCKER_COMPOSE down"
else
    echo "❌ Some services failed to start. Check logs with: $DOCKER_COMPOSE logs"
    exit 1
fi