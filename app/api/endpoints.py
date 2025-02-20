"""
API Endpoints Module

This module defines the FastAPI routes for the digital signature application.
It provides endpoints for signing PDF documents (specifically DTR - Daily Time Records)
with both owner and in-charge signatures.

The module implements secure file handling with proper cleanup, concurrent processing
for better performance, and comprehensive error handling.

Routes:
    POST /sign-dtr-owner/: Sign a DTR as an owner
    POST /sign-dtr-incharge/: Sign a DTR as an in-charge person

Security:
    - All endpoints require JWT authentication
    - Temporary files are securely handled and cleaned up
    - Concurrent processing is used for PDF signing operations
"""

import concurrent.futures
import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Response, Depends
from fastapi.responses import FileResponse
from ..core.config import settings
from ..core.security import verify_token
from ..services.pdf_signer import PDFSigner

router = APIRouter()

@router.post("/sign-dtr-owner/")
async def sign_dtr_owner(
        input_pdf: UploadFile = File(...),
        p12_file: UploadFile = File(...),
        p12_password: str = Form(...),
        image: UploadFile = File(...),
        whole_month: bool = Form(...),
        token: dict = Depends(verify_token),
):
    """
    Sign a DTR (Daily Time Record) PDF document as an owner.

    This endpoint processes a PDF document by adding an owner's digital signature.
    The signature includes both a visual representation (image) and a cryptographic
    signature using a P12/PFX certificate.

    Args:
        input_pdf (UploadFile): The PDF file to be signed
        p12_file (UploadFile): The P12/PFX certificate file for digital signing
        p12_password (str): Password for the P12/PFX certificate
        image (UploadFile): Signature image file
        whole_month (bool): Whether to sign for the whole month
        token (dict): JWT token payload (injected by dependency)

    Returns:
        Response: The signed PDF file as a downloadable attachment

    Raises:
        HTTPException: 
            - 404: If required files are not found
            - 403: If permission is denied
            - 500: For other processing errors

    Note:
        All temporary files are automatically cleaned up after processing,
        even if an error occurs.
    """
    try:
        # Create unique filenames using the original names
        input_path = os.path.join(settings.TEMP_FILE_DIR, f"input_{input_pdf.filename}")
        output_path = os.path.join(settings.TEMP_FILE_DIR, f"output_{input_pdf.filename}")
        image_path = os.path.join(settings.TEMP_FILE_DIR, f"image_{image.filename}")

        # Save uploaded files
        try:
            with open(input_path, "wb") as f:
                f.write(await input_pdf.read())

            with open(image_path, "wb") as f:
                f.write(await image.read())

            p12_data = await p12_file.read()

            # Process the PDF signing
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    PDFSigner.dtr_sign_pdf_sync_owner,
                    input_path, output_path, image_path,
                    p12_data, p12_password, whole_month
                )
                future.result()

            # Read the signed PDF
            with open(output_path, "rb") as f:
                signed_content = f.read()

            # Cleanup temporary files
            os.remove(input_path)
            os.remove(image_path)
            os.remove(output_path)

            # Return the signed PDF content
            return Response(
                content=signed_content,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="signed_{input_pdf.filename}"'
                }
            )

        finally:
            # Ensure cleanup of temporary files in case of errors
            for file_path in [input_path, image_path, output_path]:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail="Permission denied: " + str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sign-dtr-incharge/")
async def sign_dtr_incharge(
        input_pdf: UploadFile = File(...),
        p12_file: UploadFile = File(...),
        p12_password: str = Form(...),
        image: UploadFile = File(...),
        whole_month: bool = Form(...),
        token: dict = Depends(verify_token),
):
    """
    Sign a DTR (Daily Time Record) PDF document as an in-charge person.

    This endpoint processes a PDF document by adding an in-charge person's digital
    signature. The signature includes both a visual representation (image) and a
    cryptographic signature using a P12/PFX certificate.

    Args:
        input_pdf (UploadFile): The PDF file to be signed
        p12_file (UploadFile): The P12/PFX certificate file for digital signing
        p12_password (str): Password for the P12/PFX certificate
        image (UploadFile): Signature image file
        whole_month (bool): Whether to sign for the whole month
        token (dict): JWT token payload (injected by dependency)

    Returns:
        Response: The signed PDF file as a downloadable attachment

    Raises:
        HTTPException: 
            - 404: If required files are not found
            - 403: If permission is denied
            - 500: For other processing errors

    Note:
        All temporary files are automatically cleaned up after processing,
        even if an error occurs.
    """
    try:
        # Create unique filenames using the original names
        input_path = os.path.join(settings.TEMP_FILE_DIR, f"input_{input_pdf.filename}")
        output_path = os.path.join(settings.TEMP_FILE_DIR, f"output_{input_pdf.filename}")
        image_path = os.path.join(settings.TEMP_FILE_DIR, f"image_{image.filename}")

        # Save uploaded files
        try:
            with open(input_path, "wb") as f:
                f.write(await input_pdf.read())

            with open(image_path, "wb") as f:
                f.write(await image.read())

            p12_data = await p12_file.read()

            # Process the PDF signing
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    PDFSigner.dtr_sign_pdf_sync_incharge,
                    input_path, output_path, image_path,
                    p12_data, p12_password, whole_month
                )
                future.result()

            # Read the signed PDF
            with open(output_path, "rb") as f:
                signed_content = f.read()

            # Cleanup temporary files
            os.remove(input_path)
            os.remove(image_path)
            os.remove(output_path)

            # Return the signed PDF content
            return Response(
                content=signed_content,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="signed_{input_pdf.filename}"'
                }
            )

        finally:
            # Ensure cleanup of temporary files in case of errors
            for file_path in [input_path, image_path, output_path]:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail="Permission denied: " + str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
