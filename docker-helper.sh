#!/bin/bash

# Docker Development Helper Script for Shopify SaaS App

set -e

PROJECT_NAME="shopify-app"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

# Setup environment file
setup_env() {
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            print_status "Creating .env file from .env.example..."
            cp .env.example .env
            print_warning "Please edit .env file with your actual configuration values before running the application."
        else
            print_error ".env.example file not found. Please create your .env file manually."
            exit 1
        fi
    else
        print_status ".env file already exists."
    fi
}

# Build and start services
start_services() {
    print_status "Building and starting Docker services..."
    docker-compose up --build -d
    print_success "Services started successfully!"
    print_status "Frontend: http://localhost:5173"
    print_status "Backend API: http://localhost:8000"
    print_status "API Documentation: http://localhost:8000/docs"
}

# Stop services
stop_services() {
    print_status "Stopping Docker services..."
    docker-compose down
    print_success "Services stopped."
}

# View logs
show_logs() {
    if [ -z "$2" ]; then
        docker-compose logs -f
    else
        docker-compose logs -f "$2"
    fi
}

# Clean up
cleanup() {
    print_status "Cleaning up Docker resources..."
    docker-compose down -v --rmi all
    print_success "Cleanup completed."
}

# Show usage
usage() {
    echo "Docker Development Helper Script for $PROJECT_NAME"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup     - Setup environment file"
    echo "  start     - Build and start all services"
    echo "  stop      - Stop all services"
    echo "  restart   - Restart all services"
    echo "  logs      - Show logs for all services"
    echo "  logs <service> - Show logs for specific service (backend, frontend, postgres, redis, celery)"
    echo "  clean     - Stop services and remove containers, volumes, and images"
    echo "  status    - Show status of running services"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 logs backend"
    echo "  $0 stop"
}

# Main script logic
main() {
    check_docker

    case "${1:-help}" in
        setup)
            setup_env
            ;;
        start)
            setup_env
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            stop_services
            start_services
            ;;
        logs)
            show_logs "$@"
            ;;
        clean)
            cleanup
            ;;
        status)
            docker-compose ps
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            usage
            exit 1
            ;;
    esac
}

main "$@"
