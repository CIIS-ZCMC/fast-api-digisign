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

# JWT Settings
SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET environment variable must be set")

# File settings
TEMP_FILE_DIR = "temp_files"  # Directory for temporary file storage during processing
OUTPUT_DIR = "output_files"   # Directory for storing signed PDF outputs

# Create necessary directories
os.makedirs(TEMP_FILE_DIR, exist_ok=True)  # Ensure temp directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)      # Ensure output directory exists
