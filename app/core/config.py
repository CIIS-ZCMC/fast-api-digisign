import os

# JWT Settings
SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET environment variable must be set")

# File settings
TEMP_FILE_DIR = "temp_files"
OUTPUT_DIR = "output_files"

# Create necessary directories
os.makedirs(TEMP_FILE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
