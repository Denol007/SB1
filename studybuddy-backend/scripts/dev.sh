#!/bin/bash

# ============================================================================
# StudyBuddy Backend - Development Startup Script
# ============================================================================
# This script starts all required services for local development using Docker Compose
# Usage: ./scripts/dev.sh [command]
#   start       - Start all services (default)
#   stop        - Stop all services
#   restart     - Restart all services
#   logs        - Follow logs from all services
#   logs <svc>  - Follow logs from specific service
#   ps          - Show running services
#   down        - Stop and remove all containers
#   clean       - Stop, remove containers, and clean volumes
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$PROJECT_ROOT/docker"
DOCKER_COMPOSE_FILE="$DOCKER_DIR/docker-compose.yml"

# Functions
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  StudyBuddy Backend - Dev Mode${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

# Check if .env file exists
check_env() {
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        print_warning ".env file not found. Creating from .env.example..."
        if [ -f "$PROJECT_ROOT/.env.example" ]; then
            cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
            print_success ".env file created. Please configure it before running."
            print_info "Edit .env file to add your Google OAuth credentials and other settings."
        else
            print_error ".env.example file not found!"
            exit 1
        fi
    fi
}

# Start services
start_services() {
    print_header
    print_info "Starting StudyBuddy backend services..."

    cd "$PROJECT_ROOT"
    docker compose -f "$DOCKER_COMPOSE_FILE" up -d

    print_success "Services started!"
    echo ""
    print_info "Services running:"
    echo "  • API:          http://localhost:8000"
    echo "  • API Docs:     http://localhost:8000/docs"
    echo "  • ReDoc:        http://localhost:8000/redoc"
    echo "  • PostgreSQL:   localhost:5432"
    echo "  • Redis:        localhost:6379"
    echo "  • Flower:       http://localhost:5555"
    echo ""
    print_info "To view logs: ./scripts/dev.sh logs"
    print_info "To stop:      ./scripts/dev.sh stop"
}

# Stop services
stop_services() {
    print_info "Stopping StudyBuddy backend services..."
    cd "$PROJECT_ROOT"
    docker compose -f "$DOCKER_COMPOSE_FILE" stop
    print_success "Services stopped!"
}

# Restart services
restart_services() {
    print_info "Restarting StudyBuddy backend services..."
    stop_services
    start_services
}

# Show logs
show_logs() {
    cd "$PROJECT_ROOT"
    if [ -z "$1" ]; then
        docker compose -f "$DOCKER_COMPOSE_FILE" logs -f
    else
        docker compose -f "$DOCKER_COMPOSE_FILE" logs -f "$1"
    fi
}

# Show running services
show_status() {
    cd "$PROJECT_ROOT"
    docker compose -f "$DOCKER_COMPOSE_FILE" ps
}

# Down (stop and remove)
down_services() {
    print_info "Stopping and removing StudyBuddy backend containers..."
    cd "$PROJECT_ROOT"
    docker compose -f "$DOCKER_COMPOSE_FILE" down
    print_success "Containers removed!"
}

# Clean (down + remove volumes)
clean_services() {
    print_warning "This will remove all containers and data volumes!"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Cleaning up StudyBuddy backend..."
        cd "$PROJECT_ROOT"
        docker compose -f "$DOCKER_COMPOSE_FILE" down -v
        print_success "Cleanup complete!"
    else
        print_info "Cleanup cancelled."
    fi
}

# Build services
build_services() {
    print_info "Building StudyBuddy backend services..."
    cd "$PROJECT_ROOT"
    docker compose -f "$DOCKER_COMPOSE_FILE" build
    print_success "Build complete!"
}

# Main script
main() {
    check_docker
    check_env

    COMMAND="${1:-start}"

    case $COMMAND in
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        logs)
            show_logs "$2"
            ;;
        ps|status)
            show_status
            ;;
        down)
            down_services
            ;;
        clean)
            clean_services
            ;;
        build)
            build_services
            ;;
        *)
            print_error "Unknown command: $COMMAND"
            echo ""
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  start       - Start all services (default)"
            echo "  stop        - Stop all services"
            echo "  restart     - Restart all services"
            echo "  logs [svc]  - Follow logs from all or specific service"
            echo "  ps          - Show running services"
            echo "  down        - Stop and remove all containers"
            echo "  clean       - Stop, remove containers, and clean volumes"
            echo "  build       - Build/rebuild services"
            echo ""
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
