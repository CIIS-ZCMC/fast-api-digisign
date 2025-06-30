# FastAPI Digital Signature System

A robust FastAPI-based system for digitally signing PDF documents, specifically designed for Daily Time Records (DTR) and Leave Applications. The system supports secure digital signatures using PKCS#12 certificates and custom image stamps, ensuring document authenticity and regulatory compliance.

## Table of Contents
- [Features](#features)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
  - [Dependencies](#dependencies)
- [Usage](#usage)
  - [API Endpoints](#api-endpoints)
  - [Authentication](#authentication)
  - [Example Requests](#example-requests)
- [Project Structure](#project-structure)
- [Technical Implementation](#technical-implementation)
  - [Digital Signature Process](#digital-signature-process)
  - [Image Processing Workflow](#image-processing-workflow)
- [Development](#development)
- [Testing](#testing)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Versioning](#versioning)
- [License](#license)
- [Acknowledgments](#acknowledgments)
- [Recommendations and Future Improvements](#recommendations-and-future-improvements)

## Features

- **Secure Digital Signatures**: Implements PKCS#12 certificate-based digital signatures for cryptographic security and non-repudiation
- **Visual Signatures**: Supports custom signature image stamps with automatic processing for visual verification
- **Multiple Signature Types**: 
  - DTR Owner signatures (with precise positioning)
  - DTR In-charge signatures (with role-based verification)
  - Leave Application signatures (Coming Soon)
- **Image Processing**:
  - Automatic image scaling with configurable parameters
  - Background removal and transparency handling
  - Quality enhancement and DPI adjustment
  - Format conversion to RGBA for optimal rendering
- **Security**:
  - JWT-based authentication with expiration and refresh capabilities
  - Role-based access control for signature operations
  - Secure file handling with validation and sanitization
  - Automatic cleanup of temporary files to prevent data leakage
- **Performance**:
  - Concurrent processing for PDF signing operations
  - Optimized image processing with memory management
  - Efficient file handling with streaming support
  - Caching mechanisms for frequently accessed resources

## Installation

### Prerequisites

1. Download and Install Python:
   - Visit [Python's official website](https://www.python.org/downloads/)
   - Download the latest version of Python (3.12 or higher)
   - During installation, ensure you check "Add Python to PATH"
   - Verify installation by running:
     ```bash
     python --version
     ```

2. Install pip (Python package installer) if not included in Python installation:
   ```bash
   curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
   python get-pip.py
   ```

3. Virtual environment (recommended):
   - Virtualenv provides isolated Python environments
   - Helps manage dependencies for different projects
   - Prevents conflicts between package versions

4. Required system libraries:
   - OpenSSL for cryptographic operations
   - Necessary development libraries for image processing:
     ```bash
     # Ubuntu/Debian
     sudo apt-get install libssl-dev libjpeg-dev zlib1g-dev
     
     # CentOS/RHEL
     sudo yum install openssl-devel libjpeg-devel zlib-devel
     
     # Windows
     # Most dependencies are included with Python packages
     ```

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/fast-api-digisign.git
   cd fast-api-digisign
   ```

2. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Generate a secure secret key and set up environment variables:
   ```bash
   # Generate secret key using OpenSSL
   openssl rand -hex 32
   
   # Create .env file
   echo JWT_SECRET=your_generated_secret_key > .env
   echo PDF_TEMP_DIR=./temp > .env
   echo LOG_LEVEL=INFO > .env
   
   # Or set environment variables manually
   # Windows
   set JWT_SECRET=your_generated_secret_key
   set PDF_TEMP_DIR=./temp
   set LOG_LEVEL=INFO

   # Linux/macOS
   export JWT_SECRET=your_generated_secret_key
   export PDF_TEMP_DIR=./temp
   export LOG_LEVEL=INFO
   ```

5. Create required directories:
   ```bash
   mkdir -p temp/uploads temp/signed logs
   ```

### Dependencies

The system relies on the following key dependencies:

- **Web Framework and Core**:
  - fastapi>=0.68.0: FastAPI framework for building APIs
  - uvicorn>=0.15.0: ASGI server for running the application
  - python-multipart>=0.0.5: Form data handling for file uploads
  - pydantic>=2.0.0: Data validation and settings management
  - pydantic-settings>=2.0.0: Settings management with .env support

- **Authentication and Security**:
  - PyJWT>=2.10.1: JWT token handling and verification
  - cryptography>=3.4.7: Cryptographic operations for security
  - python-jose[cryptography]>=3.3.0: JWE/JWS implementation
  - passlib[bcrypt]>=1.7.4: Password hashing utilities

- **PDF Processing**:
  - pyhanko>=0.12.1: PDF signing and manipulation
  - pypdf>=3.0.0: PDF reading and writing operations
  - reportlab>=3.6.0: PDF generation and manipulation

- **Image Processing**:
  - Pillow>=10.0.0: Image processing and manipulation
  - opencv-python-headless>=4.5.0: Advanced image processing (optional)

- **Utilities**:
  - python-dateutil>=2.8.2: Date manipulation utilities
  - loguru>=0.6.0: Enhanced logging capabilities

For the complete list with exact versions, refer to `requirements.txt`.

## Usage

1. Start the server:
   ```bash
   # Development mode with auto-reload
   uvicorn main:app --reload --port 8000

   # Production mode
   uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000
   ```

2. Access the API documentation:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`
   - OpenAPI JSON: `http://localhost:8000/openapi.json`

### API Endpoints

#### Authentication

```http
POST /auth/token/
```
Obtain JWT token for API authentication.

Parameters:
- `username`: User credential
- `password`: User password

#### 1. Sign DTR as Owner
```http
POST /sign-dtr-owner/
```
Apply an owner's digital signature to a DTR document.

Parameters:
- `input_pdf`: PDF file to sign (file upload)
- `p12_file`: PKCS#12 certificate file (file upload)
- `p12_password`: Certificate password (form field)
- `image`: Signature image file (file upload, PNG/JPG)
- `whole_month`: Boolean flag for whole month signing (form field)
- `scale_factor`: Image scaling factor (optional, default: 0.9)
- `image_quality`: Output image quality (optional, default: 100)
- `signature_position`: JSON string with x,y coordinates (optional)

#### 2. Sign DTR as In-charge
```http
POST /sign-dtr-incharge/
```
Apply an in-charge's digital signature to a DTR document.

Parameters: (Same as owner endpoint, with different default signature positioning)

#### 3. Status Check
```http
GET /status/
```
Check the API service status and version information.

#### 4. Verify Signature
```http
POST /verify-signature/
```
Verify the authenticity of a signed PDF document.

Parameters:
- `signed_pdf`: Signed PDF file to verify (file upload)

### Authentication

All endpoints except `/status/` and authentication endpoints require JWT authentication. Include the token in the Authorization header:

```http
Authorization: Bearer <your_jwt_token>
```

The JWT token has a configurable expiration time (default: 30 minutes). After expiration, a new token must be requested.

### Example Requests

#### cURL Examples

1. Authenticate and get token:
```bash
curl -X POST "http://localhost:8000/auth/token/" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=yourpassword"
```

2. Sign a DTR as owner:
```bash
curl -X POST "http://localhost:8000/sign-dtr-owner/" \
  -H "Authorization: Bearer your_jwt_token" \
  -F "input_pdf=@path/to/document.pdf" \
  -F "p12_file=@path/to/certificate.p12" \
  -F "p12_password=your_certificate_password" \
  -F "image=@path/to/signature.png" \
  -F "whole_month=true" \
  -F "scale_factor=0.8"
```

#### Python Example

```python
import requests

# Authenticate
auth_response = requests.post(
    "http://localhost:8000/auth/token/",
    data={"username": "admin", "password": "yourpassword"}
)
token = auth_response.json()["access_token"]

# Sign document
with open("document.pdf", "rb") as pdf_file, \
     open("certificate.p12", "rb") as p12_file, \
     open("signature.png", "rb") as img_file:
    
    response = requests.post(
        "http://localhost:8000/sign-dtr-owner/",
        headers={"Authorization": f"Bearer {token}"},
        files={
            "input_pdf": pdf_file,
            "p12_file": p12_file,
            "image": img_file
        },
        data={
            "p12_password": "your_certificate_password",
            "whole_month": "true",
            "scale_factor": "0.8"
        }
    )

# Save the signed PDF
if response.status_code == 200:
    with open("signed_document.pdf", "wb") as f:
        f.write(response.content)
```

## Project Structure

```
fast-api-digisign/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── endpoints.py          # API route definitions
│   │   ├── dependencies.py       # FastAPI dependencies
│   │   └── models.py             # Request/Response models
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py             # Configuration settings
│   │   ├── security.py           # Authentication & security
│   │   └── exceptions.py         # Custom exceptions
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pdf_signer.py         # PDF signing logic
│   │   └── certificate_manager.py # Certificate handling
│   └── utils/
│       ├── __init__.py
│       ├── auth.py               # Authentication utilities
│       ├── image_processor.py    # Image processing tools
│       └── file_handler.py       # File operations
├── tests/
│   ├── __init__.py
│   ├── test_api.py               # API tests
│   ├── test_pdf_signer.py        # PDF signing tests
│   └── test_image_processor.py   # Image processing tests
├── static/                       # Static files
├── temp/                         # Temporary file storage
│   ├── uploads/                  # Upload directory
│   └── signed/                   # Signed documents
├── logs/                         # Log files
├── .env                          # Environment variables
├── .gitignore                    # Git ignore file
├── main.py                       # Application entry point
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Docker configuration
├── docker-compose.yml            # Docker Compose configuration
└── README.md                     # Project documentation
```

## Technical Implementation

### Digital Signature Process

1. **Document Preparation**:
   - The system validates the uploaded PDF for format compliance
   - Temporary copies are created to prevent modifying the original

2. **Certificate Handling**:
   - PKCS#12 certificates are securely loaded with the provided password
   - The certificate is validated for expiration and trust chain

3. **Signature Application Process**:
   - The system determines signature coordinates based on document type and role
   - For DTRs, different positioning is used for owner vs in-charge signatures
   - When "whole_month" is enabled, signatures are applied to all relevant fields

4. **Cryptographic Security**:
   - Digital signatures include a cryptographic hash of the document
   - Signatures are embedded with timestamp information for validation
   - The process follows industry-standard PDF signing practices

### Image Processing Workflow

1. **Image Preprocessing**:
   - Uploaded signature images are validated for format and size
   - Background removal is applied for non-transparent images
   - Resolution is adjusted for optimal display in PDFs

2. **Scaling and Positioning**:
   - Images are scaled according to the provided scale factor
   - Aspect ratio is maintained to prevent distortion
   - Default positioning is applied based on document type and role

3. **Format Conversion**:
   - All images are converted to RGBA format for consistent processing
   - Transparency is preserved throughout the pipeline
   - Quality settings are applied based on user preferences

## Development

The system architecture follows these principles:

- **FastAPI's Dependency Injection**: Used for clean architecture and testability
- **Service-Oriented Design**: Core functionality is isolated in service modules
- **Asynchronous Processing**: Leverages Python's async capabilities for performance
- **Middleware Pipeline**: Request processing includes validation, authentication, and logging
- **Comprehensive Error Handling**: Structured exception handling with detailed error responses
- **Automatic Documentation**: OpenAPI schema generation for all endpoints

Development Guidelines:

1. Use virtual environments for isolated development
2. Follow PEP 8 style guidelines for Python code
3. Write tests for all new features and bug fixes
4. Document code with docstrings and type hints
5. Use git branches for feature development

## Testing

The project includes comprehensive tests to ensure reliability:

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Verify interaction between components
3. **API Tests**: Test the API endpoints directly

Run tests using pytest:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_pdf_signer.py

# Run with coverage report
pytest --cov=app tests/
```

## Security Considerations

1. Always use HTTPS in production environments
2. Keep your JWT secret key secure and rotate regularly
3. Regularly update dependencies to patch security vulnerabilities
4. Monitor system logs for unauthorized access attempts
5. Implement rate limiting in production to prevent abuse
6. Use secure file handling practices:
   - Validate file types and contents
   - Limit file sizes
   - Use temporary storage with automatic cleanup
7. Store sensitive information like certificates securely
8. Implement IP-based access controls for production deployments
9. Consider using a Web Application Firewall (WAF)

## Troubleshooting

Common issues and solutions:

1. **Certificate Loading Failures**:
   - Verify the password is correct
   - Ensure the P12 file is valid and not corrupted
   - Check certificate expiration date

2. **Image Processing Issues**:
   - Try different image formats (PNG recommended)
   - Adjust scale_factor for better positioning
   - Use images with transparent backgrounds for best results

3. **API Connection Problems**:
   - Verify the server is running
   - Check network connectivity
   - Ensure the JWT token is valid and not expired

4. **PDF Signing Failures**:
   - Verify the PDF is not protected or encrypted
   - Check that the PDF follows the standard format
   - Ensure sufficient disk space for temporary files

For additional help, check the logs in the `logs/` directory or enable debug logging by setting `LOG_LEVEL=DEBUG` in the environment variables.

## Contributing

We welcome contributions to improve the FastAPI Digital Signature System:

1. Fork the repository on GitHub
2. Create a feature branch from the `develop` branch
3. Follow the coding style and add appropriate tests
4. Commit your changes with clear commit messages
5. Push to your branch and create a Pull Request
6. Ensure CI tests pass on your Pull Request

## Recommendations and Future Improvements

### Code Organization

1. **Modular Endpoint Structure**: Refactor API endpoints into separate router modules by functionality (authentication, signing, verification, etc.) to improve maintainability as the system grows.

2. **Dependency Container Pattern**: Implement a dependency container to manage service instantiation and dependency injection more systematically.

3. **Interface-based Design**: Create interfaces for core services to enhance testability and allow for alternative implementations.

4. **Configuration Management**: Move from environment variables to a more structured configuration system with validation and environment-specific profiles.

5. **Layer Separation**: Strengthen the separation between API, service, and data access layers with clear boundaries and interfaces.

### Performance Enhancements

1. **Background Processing**: Implement asynchronous processing with task queues for signature operations on large documents or batch operations.

2. **Caching Layer**: Add caching for frequently accessed resources and computation results.

3. **Connection Pooling**: Implement connection pooling for any database or external service interactions.

4. **Optimize Image Processing**: Further optimize image processing pipeline with parallel processing and improved algorithms.

### Security Improvements

1. **Enhanced Authentication**: Add support for OAuth2 with multiple authentication providers.

2. **Certificate Management**: Implement a certificate management system for storing and retrieving certificates securely.

3. **Audit Logging**: Add comprehensive audit logging for all signature operations.

4. **API Rate Limiting**: Implement token bucket or leaky bucket algorithms for more sophisticated rate limiting.

5. **Certificate Verification Chain**: Add support for full certificate chain verification against trusted certificate authorities.

### Feature Additions

1. **Batch Processing**: Support for signing multiple documents in a single request.

2. **Signature Templates**: Allow users to save and reuse signature templates with predefined positions.

3. **Document Metadata**: Extract and preserve document metadata during signing operations.

4. **Signature Workflow**: Implement multi-step signature workflows with approvals and notifications.

5. **Signature Verification API**: Enhance the verification API to provide detailed information about signature validity.

6. **PDF Form Field Support**: Add capabilities to detect and interact with PDF form fields.

7. **Mobile Support**: Develop a companion mobile application for capturing signatures on mobile devices.

### Infrastructure and DevOps

1. **Containerization**: Enhance Docker setup with multi-stage builds and optimized container sizes.

2. **CI/CD Pipeline**: Implement a complete CI/CD pipeline with automated testing and deployment.

3. **Monitoring**: Add application monitoring with metrics, tracing, and alerting.

4. **Horizontal Scaling**: Optimize for horizontal scaling in containerized environments.

5. **Infrastructure as Code**: Implement infrastructure as code for deployment environments.

### Documentation

1. **API Versioning Documentation**: Add comprehensive documentation for API versioning and deprecation policies.

2. **Integration Examples**: Provide code examples for integrating with common languages and frameworks.

3. **Architecture Documentation**: Create detailed architecture documentation with component diagrams.

4. **Performance Benchmarks**: Document performance characteristics and benchmarks.

## Versioning

This project follows [Semantic Versioning](https://semver.org/):

- Major version: Incompatible API changes
- Minor version: New features in a backward-compatible manner
- Patch version: Backward-compatible bug fixes

Release history is documented in the CHANGELOG.md file.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [PyHanko](https://pyhanko.readthedocs.io/) for PDF signing functionality
- [Pillow](https://python-pillow.org/) for image processing capabilities
- All contributors who have helped improve this project
