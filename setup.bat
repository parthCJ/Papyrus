@echo off
echo ResearchRAG - Setup Script
echo ==========================
echo.

echo Step 1: Creating directories...
if not exist "data\raw" mkdir "data\raw"
if not exist "data\processed" mkdir "data\processed"
if not exist "data\sample_papers" mkdir "data\sample_papers"
echo Directories created.
echo.

echo Step 2: Setting up environment file...
cd backend
if not exist ".env" (
    copy ".env.example" ".env"
    echo Created .env file from .env.example
    echo Please review and update .env if needed.
) else (
    echo .env file already exists.
)
cd ..
echo.

echo Step 3: Starting Docker services...
docker-compose up -d elasticsearch ollama
echo Waiting for services to start...
timeout /t 10 /nobreak > nul
echo.

echo Step 4: Checking Elasticsearch...
:check_elasticsearch
curl -s http://localhost:9200/_cluster/health > nul 2>&1
if errorlevel 1 (
    echo Waiting for Elasticsearch...
    timeout /t 5 /nobreak > nul
    goto check_elasticsearch
)
echo Elasticsearch is ready!
echo.

echo Step 5: Pulling Ollama model...
docker exec -it research-rag-ollama ollama pull llama3.2
echo Ollama model ready!
echo.

echo Step 6: Installing Python dependencies...
cd backend
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
cd ..
echo.

echo ==========================
echo Setup Complete!
echo ==========================
echo.
echo To start the backend:
echo   cd backend
echo   venv\Scripts\activate.bat
echo   uvicorn app.main:app --reload
echo.
echo Or use Docker Compose:
echo   docker-compose up -d
echo.
echo API Documentation: http://localhost:8000/docs
echo Elasticsearch: http://localhost:9200
echo Ollama: http://localhost:11434
echo.
pause
