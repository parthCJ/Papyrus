"""
Hugging Face Spaces entry point
This file is required for HF Spaces deployment
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from backend.app.main import app

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 7860))  # HF Spaces uses port 7860
    uvicorn.run(app, host="0.0.0.0", port=port)
