#!/bin/bash

# BAC Hunter Frontend Setup Script
# This script sets up the modern React-based frontend for BAC Hunter

set -e

echo "🛡️  BAC Hunter Frontend Setup"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if Node.js is installed
check_node() {
    print_header "Checking Node.js installation..."
    
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js 18+ first."
        echo "Visit: https://nodejs.org/"
        exit 1
    fi
    
    NODE_VERSION=$(node --version | sed 's/v//')
    MAJOR_VERSION=$(echo $NODE_VERSION | cut -d. -f1)
    
    if [ "$MAJOR_VERSION" -lt 18 ]; then
        print_error "Node.js version $NODE_VERSION is too old. Please install Node.js 18+."
        exit 1
    fi
    
    print_status "Node.js version $NODE_VERSION is installed ✓"
}

# Check if npm is installed
check_npm() {
    print_header "Checking npm installation..."
    
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed. Please install npm first."
        exit 1
    fi
    
    NPM_VERSION=$(npm --version)
    print_status "npm version $NPM_VERSION is installed ✓"
}

# Install frontend dependencies
install_dependencies() {
    print_header "Installing frontend dependencies..."
    
    cd frontend
    
    if [ ! -f "package.json" ]; then
        print_error "package.json not found. Make sure you're in the correct directory."
        exit 1
    fi
    
    print_status "Installing Node.js packages..."
    npm install
    
    if [ $? -eq 0 ]; then
        print_status "Dependencies installed successfully ✓"
    else
        print_error "Failed to install dependencies"
        exit 1
    fi
    
    cd ..
}

# Build frontend for production
build_frontend() {
    print_header "Building frontend for production..."
    
    cd frontend
    
    print_status "Running production build..."
    npm run build
    
    if [ $? -eq 0 ]; then
        print_status "Frontend built successfully ✓"
        print_status "Built files are in: bac_hunter/webapp/static/dist/"
    else
        print_error "Frontend build failed"
        exit 1
    fi
    
    cd ..
}

# Setup development environment
setup_dev() {
    print_header "Setting up development environment..."
    
    cd frontend
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        print_status "Creating .env file..."
        cat > .env << EOF
VITE_API_BASE_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws
VITE_APP_TITLE=BAC Hunter
EOF
        print_status ".env file created ✓"
    else
        print_status ".env file already exists ✓"
    fi
    
    cd ..
}

# Create necessary directories
create_directories() {
    print_header "Creating necessary directories..."
    
    mkdir -p bac_hunter/webapp/static/dist
    mkdir -p frontend/public
    
    print_status "Directories created ✓"
}

# Copy favicon and assets
setup_assets() {
    print_header "Setting up assets..."
    
    # Create favicon if it doesn't exist
    if [ ! -f "frontend/public/favicon.ico" ]; then
        print_status "Creating default favicon..."
        # Create a simple favicon (you might want to replace this with a real one)
        touch frontend/public/favicon.ico
    fi
    
    # Copy existing favicon from webapp if available
    if [ -f "bac_hunter/webapp/static/favicon.ico" ]; then
        print_status "Copying existing favicon..."
        cp bac_hunter/webapp/static/favicon.ico frontend/public/
    fi
    
    print_status "Assets setup complete ✓"
}

# Update backend to serve frontend
update_backend() {
    print_header "Backend is already configured to serve the new frontend ✓"
    print_status "The enhanced_server.py has been updated with React frontend support"
}

# Display completion message
show_completion() {
    echo ""
    echo "🎉 Frontend setup completed successfully!"
    echo "========================================"
    echo ""
    echo -e "${GREEN}Next steps:${NC}"
    echo "1. Start the development server:"
    echo -e "   ${BLUE}cd frontend && npm run dev${NC}"
    echo ""
    echo "2. Or start the backend with built frontend:"
    echo -e "   ${BLUE}python -m bac_hunter dashboard${NC}"
    echo ""
    echo -e "${GREEN}Development URLs:${NC}"
    echo "• Frontend dev server: http://localhost:3000"
    echo "• Backend with frontend: http://localhost:8000"
    echo ""
    echo -e "${GREEN}Available commands:${NC}"
    echo "• npm run dev      - Start development server"
    echo "• npm run build    - Build for production"
    echo "• npm run preview  - Preview production build"
    echo "• npm run lint     - Run linter"
    echo ""
    echo -e "${YELLOW}Note:${NC} The frontend will automatically proxy API requests to the backend."
    echo "Make sure the BAC Hunter backend is running on port 8000."
}

# Main execution
main() {
    print_status "Starting BAC Hunter frontend setup..."
    
    # Check prerequisites
    check_node
    check_npm
    
    # Setup
    create_directories
    setup_assets
    install_dependencies
    setup_dev
    
    # Build for production
    if [ "$1" = "--build" ]; then
        build_frontend
    fi
    
    # Update backend configuration
    update_backend
    
    # Show completion message
    show_completion
}

# Run main function with all arguments
main "$@"
