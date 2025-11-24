"""
Core Configuration Module

This module manages the core configuration settings for the FastAPI Digital Signature
application. It handles environment variables, directory setup, and other global
configuration parameters.

Configuration includes:
- JWT authentication settings
- File storage directories for temporary and output files
- Automatic creation of required directories

Environment Variables:
    JWT_SECRET: Required. The secret key used for JWT token signing
"""

import os

# Optional: load .env for local development if python-dotenv is installed
try:
    from dotenv import load_dotenv
    # Load .env from project root (two levels above this file: project_root/.env)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    load_dotenv(os.path.join(project_root, ".env"))
except Exception:
    # dotenv not installed or .env not present — ignore for production
    # If python-dotenv is not available, we'll try a lightweight manual parser
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    env_path = os.path.join(project_root, ".env")
    try:
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for raw in f:
                    line = raw.strip()
                    # skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        # only set if not already in environment
                        if k and k not in os.environ:
                            os.environ[k] = v
    except Exception:
        # If manual parsing fails, ignore — we'll raise below when SECRET_KEY missing
        pass

# JWT Settings
SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET environment variable must be set; see .env.example for development")

# File settings
TEMP_FILE_DIR = "temp_files"  # Directory for temporary file storage during processing
OUTPUT_DIR = "output_files"   # Directory for storing signed PDF outputs

# Create necessary directories
os.makedirs(TEMP_FILE_DIR, exist_ok=True)  # Ensure temp directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)      # Ensure output directory exists
