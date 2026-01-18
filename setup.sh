#!/bin/bash

echo "ResearchRAG - Setup Script"
echo "=========================="
echo ""

echo "Step 1: Creating directories..."
mkdir -p data/raw
mkdir -p data/processed
mkdir -p data/sample_papers
echo "Directories created."
echo ""

echo "Step 2: Setting up environment file..."
cd backend
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file from .env.example"
    echo "Please review and update .env if needed."
else
    echo ".env file already exists."
fi
cd ..
echo ""

echo "Step 3: Starting Docker services..."
docker-compose up -d elasticsearch ollama
echo "Waiting for services to start..."
sleep 10
echo ""

echo "Step 4: Checking Elasticsearch..."
until curl -s http://localhost:9200/_cluster/health > /dev/null; do
    echo "Waiting for Elasticsearch..."
    sleep 5
done
echo "Elasticsearch is ready!"
echo ""

echo "Step 5: Pulling Ollama model..."
docker exec -it research-rag-ollama ollama pull llama3.2
echo "Ollama model ready!"
echo ""

echo "Step 6: Installing Python dependencies..."
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..
echo ""

echo "=========================="
echo "Setup Complete!"
echo "=========================="
echo ""
echo "To start the backend:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload"
echo ""
echo "Or use Docker Compose:"
echo "  docker-compose up -d"
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo "Elasticsearch: http://localhost:9200"
echo "Ollama: http://localhost:11434"
