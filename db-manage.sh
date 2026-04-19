#!/bin/bash

# Database Management Script for Learn Your Way
# This script provides utilities for managing the PostgreSQL database

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Default values
POSTGRES_USER=${POSTGRES_USER:-postgres}
POSTGRES_DB=${POSTGRES_DB:-lear_your_way}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres123}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🐘 Learn Your Way Database Management${NC}"
echo "=================================="

show_help() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  status     - Show database connection status"
    echo "  shell      - Open PostgreSQL shell"
    echo "  backup     - Create database backup"
    echo "  restore    - Restore database from backup"
    echo "  reset      - Reset database (WARNING: deletes all data)"
    echo "  migrate    - Run database migrations"
    echo "  logs       - Show PostgreSQL container logs"
    echo "  help       - Show this help message"
}

check_docker() {
    if ! docker ps > /dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
        exit 1
    fi
}

check_container() {
    if ! docker ps | grep -q lear_your_way_postgres; then
        echo -e "${RED}❌ PostgreSQL container is not running. Start it with: docker-compose up -d postgres${NC}"
        exit 1
    fi
}

db_status() {
    echo -e "${YELLOW}📊 Checking database status...${NC}"
    check_docker
    check_container

    echo "Database Configuration:"
    echo "  Host: localhost"
    echo "  Port: 5432"
    echo "  Database: $POSTGRES_DB"
    echo "  User: $POSTGRES_USER"
    echo ""

    if docker exec lear_your_way_postgres pg_isready -U $POSTGRES_USER -d $POSTGRES_DB > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Database is ready and accepting connections${NC}"

        # Show database size and table count
        echo ""
        echo "Database Information:"
        docker exec lear_your_way_postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c "
            SELECT
                pg_database.datname as database_name,
                pg_size_pretty(pg_database_size(pg_database.datname)) as size,
                (SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public') as table_count
            FROM pg_database
            WHERE pg_database.datname = '$POSTGRES_DB';
        " 2>/dev/null || echo "  Could not retrieve detailed info"
    else
        echo -e "${RED}❌ Database is not ready${NC}"
    fi
}

db_shell() {
    echo -e "${YELLOW}🐚 Opening PostgreSQL shell...${NC}"
    check_docker
    check_container
    docker exec -it lear_your_way_postgres psql -U $POSTGRES_USER -d $POSTGRES_DB
}

db_backup() {
    echo -e "${YELLOW}💾 Creating database backup...${NC}"
    check_docker
    check_container

    BACKUP_FILE="backup_${POSTGRES_DB}_$(date +%Y%m%d_%H%M%S).sql"
    docker exec lear_your_way_postgres pg_dump -U $POSTGRES_USER -d $POSTGRES_DB > "./backups/$BACKUP_FILE"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Backup created: ./backups/$BACKUP_FILE${NC}"
    else
        echo -e "${RED}❌ Backup failed${NC}"
        exit 1
    fi
}

db_restore() {
    if [ -z "$1" ]; then
        echo -e "${RED}❌ Please provide backup file path${NC}"
        echo "Usage: $0 restore <backup_file>"
        exit 1
    fi

    if [ ! -f "$1" ]; then
        echo -e "${RED}❌ Backup file not found: $1${NC}"
        exit 1
    fi

    echo -e "${YELLOW}🔄 Restoring database from $1...${NC}"
    check_docker
    check_container

    # Copy backup file to container
    docker cp "$1" lear_your_way_postgres:/tmp/restore.sql

    # Restore database
    docker exec lear_your_way_postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -f /tmp/restore.sql

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Database restored successfully${NC}"
        # Clean up
        docker exec lear_your_way_postgres rm /tmp/restore.sql
    else
        echo -e "${RED}❌ Database restore failed${NC}"
        exit 1
    fi
}

db_reset() {
    echo -e "${RED}⚠️  WARNING: This will delete all data in the database!${NC}"
    read -p "Are you sure you want to continue? (type 'yes' to confirm): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo -e "${YELLOW}🔄 Resetting database...${NC}"
        check_docker
        check_container

        # Drop and recreate database
        docker exec lear_your_way_postgres psql -U postgres -c "DROP DATABASE IF EXISTS $POSTGRES_DB;"
        docker exec lear_your_way_postgres psql -U postgres -c "CREATE DATABASE $POSTGRES_DB;"

        echo -e "${GREEN}✅ Database reset successfully${NC}"
        echo "You can now run migrations to recreate the schema."
    else
        echo "Operation cancelled."
    fi
}

db_migrate() {
    echo -e "${YELLOW}🔄 Running database migrations...${NC}"
    check_docker
    check_container

    # Restart backend to trigger SQLAlchemy auto-creation
    docker-compose restart backend

    echo -e "${GREEN}✅ Migrations completed${NC}"
}

db_logs() {
    echo -e "${YELLOW}📋 Showing PostgreSQL logs...${NC}"
    check_docker

    if docker ps | grep -q lear_your_way_postgres; then
        docker logs -f lear_your_way_postgres
    else
        echo -e "${RED}❌ PostgreSQL container is not running${NC}"
    fi
}

# Create backups directory if it doesn't exist
mkdir -p backups

# Main command handling
case "${1:-help}" in
    "status")
        db_status
        ;;
    "shell")
        db_shell
        ;;
    "backup")
        db_backup
        ;;
    "restore")
        db_restore "$2"
        ;;
    "reset")
        db_reset
        ;;
    "migrate")
        db_migrate
        ;;
    "logs")
        db_logs
        ;;
    "help"|*)
        show_help
        ;;
esac