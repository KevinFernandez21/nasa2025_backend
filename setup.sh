#!/bin/bash

# Setup script for NASA 2025 Backend
# This script helps set up the development environment

set -e

echo "🚀 NASA 2025 Backend - Setup Script"
echo "===================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ .env created! Please edit it with your credentials."
    echo ""
else
    echo "✅ .env file already exists"
    echo ""
fi

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo "🐍 Python version: $PYTHON_VERSION"
else
    echo "❌ Python 3 not found. Please install Python 3.12+"
    exit 1
fi

# Install dependencies
echo ""
read -p "📦 Install Python dependencies? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -d "venv" ]; then
        echo "✅ Virtual environment already exists"
    else
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi

    echo "Activating virtual environment..."
    source venv/bin/activate

    echo "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt

    echo "✅ Dependencies installed!"
fi

# Check Docker
echo ""
if command -v docker &> /dev/null; then
    echo "🐳 Docker version: $(docker --version)"

    read -p "🐳 Build Docker image? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Building Docker image..."
        docker build -t nasa-backend .
        echo "✅ Docker image built!"
    fi
else
    echo "⚠️  Docker not found. Install Docker to use containerization."
fi

# Summary
echo ""
echo "======================================"
echo "✅ Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your credentials"
echo "2. Run locally:"
echo "   - Python: uvicorn app.main:app --reload --port 8080"
echo "   - Docker: docker-compose up"
echo ""
echo "3. Deploy to Google Cloud:"
echo "   - gcloud builds submit --config cloudbuild.yaml"
echo ""
echo "📚 Documentation:"
echo "   - README.md - Getting started"
echo "   - API_REFERENCE.md - API docs"
echo "   - DEPLOYMENT.md - Deployment guide"
echo "   - COMMANDS.md - Useful commands"
echo ""
echo "Happy coding! 🎉"
