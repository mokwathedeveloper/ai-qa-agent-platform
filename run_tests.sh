#!/bin/bash

# System Test Runner Script
# This script starts the backend, frontend, and runs comprehensive tests

set -e

echo "🚀 Starting AI QA Agent Platform System Tests"
echo "=============================================="

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

# Check if we're in the right directory
if [ ! -f "backend/main.py" ] || [ ! -f "frontend/package.json" ]; then
    print_error "Please run this script from the ai-qa-agent-platform root directory"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    print_error "Node.js is required but not installed"
    exit 1
fi

# Install Python dependencies if needed
print_status "Checking Python dependencies..."
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install required packages for testing
pip install -q websockets requests

# Install backend dependencies
if [ -f "requirements.txt" ]; then
    print_status "Installing backend dependencies..."
    pip install -q -r requirements.txt
fi

# Install frontend dependencies
print_status "Checking frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    print_status "Installing frontend dependencies..."
    npm install
fi
cd ..

# Start backend in background
print_status "Starting backend server..."
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to start
print_status "Waiting for backend to start..."
sleep 5

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    print_error "Backend failed to start"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

print_success "Backend started successfully (PID: $BACKEND_PID)"

# Start frontend in background
print_status "Starting frontend server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
print_status "Waiting for frontend to start..."
sleep 10

# Check if frontend is running
if ! curl -s http://localhost:3000 > /dev/null; then
    print_warning "Frontend may not be fully ready yet"
fi

print_success "Frontend started successfully (PID: $FRONTEND_PID)"

# Run system tests
print_status "Running system integration tests..."
python test_system.py

# Open test pages in browser (if available)
if command -v xdg-open &> /dev/null; then
    print_status "Opening test interfaces..."
    xdg-open http://localhost:3000 &
    xdg-open file://$(pwd)/frontend_test.html &
elif command -v open &> /dev/null; then
    print_status "Opening test interfaces..."
    open http://localhost:3000 &
    open file://$(pwd)/frontend_test.html &
fi

echo ""
echo "=============================================="
print_success "System is running! Test interfaces:"
echo "  • Main App: http://localhost:3000"
echo "  • Backend API: http://localhost:8000"
echo "  • Network Monitor: file://$(pwd)/frontend_test.html"
echo ""
print_status "Press Ctrl+C to stop all services"
echo "=============================================="

# Function to cleanup on exit
cleanup() {
    echo ""
    print_status "Shutting down services..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    print_success "All services stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Keep script running
while true; do
    sleep 1
done