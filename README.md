# FastAPI Digital Signature System

A robust FastAPI-based system for digitally signing PDF documents, specifically designed for Daily Time Records (DTR) and Leave Applications. The system supports secure digital signatures using PKCS#12 certificates and custom image stamps, ensuring document authenticity and regulatory compliance.

## Features

- **Secure Digital Signatures**: Implements PKCS#12 certificate-based digital signatures
- **Visual Signatures**: Supports custom signature image stamps with automatic processing
- **Multiple Signature Types**: 
  - DTR Owner signatures
  - DTR In-charge signatures
  - Leave Application signatures (Coming Soon)
- **Image Processing**:
  - Automatic image scaling
  - Quality enhancement
  - Format conversion to RGBA
- **Security**:
  - JWT-based authentication
  - Secure file handling
  - Automatic cleanup of temporary files
- **Performance**:
  - Concurrent processing for PDF signing
  - Optimized image processing
  - Efficient file handling

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

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

4. Set up environment variables:
   ```bash
   # Windows
   set JWT_SECRET=your_secret_key

   # Linux/macOS
   export JWT_SECRET=your_secret_key
   ```

### Dependencies

- fastapi>=0.68.0: FastAPI framework
- uvicorn>=0.15.0: ASGI server
- python-multipart>=0.0.5: Form data handling
- PyJWT>=2.10.1: JWT token handling
- cryptography>=3.4.7: Cryptographic operations
- pyhanko>=0.12.1: PDF signing
- pydantic>=2.0.0: Data validation
- pydantic-settings>=2.0.0: Settings management
- Pillow>=10.0.0: Image processing

## Usage

1. Start the server:
   ```bash
   uvicorn main:app --reload
   ```

2. Access the API documentation:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

### API Endpoints

#### 1. Sign DTR as Owner
```http
POST /sign-dtr-owner/
```
Parameters:
- `input_pdf`: PDF file to sign
- `p12_file`: PKCS#12 certificate file
- `p12_password`: Certificate password
- `image`: Signature image file
- `whole_month`: Boolean flag for whole month signing
- `scale_factor`: Image scaling factor (optional, default: 0.9)
- `image_quality`: Output image quality (optional, default: 100)

#### 2. Sign DTR as In-charge
```http
POST /sign-dtr-incharge/
```
Parameters: (Same as owner endpoint)

### Authentication

All endpoints require JWT authentication. Include the token in the Authorization header:
```http
Authorization: Bearer <your_jwt_token>
```

## Project Structure

```
fast-api-digisign/
├── app/
│   ├── api/
│   │   └── endpoints.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── services/
│   │   └── pdf_signer.py
│   └── utils/
│       ├── auth.py
│       └── image_processor.py
├── main.py
├── requirements.txt
└── README.md
```

## Development

- The system uses FastAPI's dependency injection for clean architecture
- Implements concurrent processing for PDF signing operations
- Includes comprehensive error handling and cleanup procedures
- Features automatic temporary file management

## Security Considerations

1. Always use HTTPS in production
2. Keep your JWT secret key secure
3. Regularly update dependencies
4. Monitor system logs for unauthorized access attempts
5. Implement rate limiting in production
6. Use secure file handling practices

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
