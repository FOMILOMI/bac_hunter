#!/bin/bash

# BAC Hunter Quick Start Script
# This script automates the installation and setup of BAC Hunter

set -e  # Exit on any error

echo "🚀 BAC Hunter Quick Start Script"
echo "=================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python version: $PYTHON_VERSION"

# Install system dependencies if needed
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "📦 Installing system dependencies..."
    sudo apt update
    sudo apt install -y python3-venv python3-pip curl
fi

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing BAC Hunter dependencies..."
if [ "$1" = "minimal" ]; then
    echo "Installing minimal dependencies..."
    pip install -r requirements-minimal.txt
else
    echo "Installing full dependencies..."
    pip install -r requirements-fixed.txt
fi

# Verify installation
echo "🔍 Verifying installation..."
python -m bac_hunter doctor

echo ""
echo "✅ Installation complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run the setup wizard: python -m bac_hunter setup-wizard"
echo "3. Start scanning: python -m bac_hunter quickscan https://example.com"
echo "4. Or start the dashboard: python -m bac_hunter dashboard"
echo ""
echo "📚 For more information, see INSTALLATION_GUIDE.md"
echo ""