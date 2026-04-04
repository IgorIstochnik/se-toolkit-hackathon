#!/bin/bash
# Deployment script for Matrix Cafe Menu Helper

set -e

echo "🍽️  Matrix Cafe Menu Helper - Deployment Script"
echo "================================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose is not installed."
    exit 1
fi

echo "✅ Docker found: $(docker --version)"
echo "✅ Docker Compose found: $(docker compose version)"

# Build and start services
echo ""
echo "📦 Building services..."
docker compose build

echo ""
echo "🚀 Starting services..."
docker compose up -d

echo ""
echo "✅ Services started!"
echo ""
echo "📋 Running containers:"
docker compose ps

echo ""
echo "💡 To interact with the bot:"
echo "   docker attach matrix-cafe-bot"
echo ""
echo "📊 To view logs:"
echo "   docker compose logs -f"
echo ""
echo "🛑 To stop services:"
echo "   docker compose down"
