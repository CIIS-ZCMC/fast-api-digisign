"""
FastAPI Digital Signature Application

This module implements a FastAPI-based web service for digitally signing PDF documents,
specifically designed for handling DTR (Daily Time Record) signatures. It provides
endpoints for both owner and in-charge signatures, with support for image processing
and digital certificate-based signing.

The application handles:
- PDF document uploading and signing
- Digital certificate (P12) processing
- Signature image processing and scaling
- Concurrent processing for better performance
- Temporary file management
"""

import concurrent.futures
import os
import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import FileResponse
from app.utils.auth import verify_token
from app.services.pdf_signer import PDFSigner
from app.utils.image_processor import ImageProcessor
from app.core.config import TEMP_FILE_DIR, OUTPUT_DIR

app = FastAPI(
    title="Digital Signature API",
    description="API for digitally signing PDF documents with image and certificate-based signatures",
    version="1.0.0"
)

@app.post("/sign-dtr-owner/")
async def sign_dtr_owner(
        input_pdf: UploadFile = File(...),
        p12_file: UploadFile = File(...),
        p12_password: str = Form(...),
        image: UploadFile = File(...),
        whole_month: bool = Form(...),
        scale_factor: float = Form(0.9),  # 0.9 = 90% of original size (10% reduction)
        image_quality: int = Form(100),    # 100% quality
        token: dict = Depends(verify_token),
):
    """
    Sign a DTR (Daily Time Record) PDF as an owner with a digital signature.

    Parameters:
        input_pdf (UploadFile): The PDF file to be signed
        p12_file (UploadFile): The P12/PFX certificate file for digital signing
        p12_password (str): Password for the P12/PFX certificate
        image (UploadFile): Signature image file (PNG format recommended)
        whole_month (bool): Whether to sign for the whole month or specific dates
        scale_factor (float): Scaling factor for the signature image (default: 0.9)
        image_quality (int): Quality of the processed signature image (default: 100)
        token (dict): Authentication token (automatically injected by dependency)

    Returns:
        FileResponse: The signed PDF file

    Raises:
        HTTPException: 
            - 404: If required files are not found
            - 403: If permission is denied
            - 500: For other processing errors
    """
    try:
        # Generate unique filenames with timestamp
        timestamp = int(datetime.datetime.now().timestamp())
        output_pdf = f"signed_owner_{timestamp}.pdf"
        input_path = os.path.join(TEMP_FILE_DIR, f"input_{timestamp}.pdf")
        output_path = os.path.join(OUTPUT_DIR, output_pdf)
        
        # Image paths
        original_image_path = os.path.join(TEMP_FILE_DIR, f"original_image_{timestamp}.png")
        processed_image_path = os.path.join(TEMP_FILE_DIR, f"processed_image_{timestamp}.png")

        # Save uploaded files to temp directory
        with open(input_path, "wb") as f:
            f.write(await input_pdf.read())

        with open(original_image_path, "wb") as f:
            f.write(await image.read())

        # Process the image
        ImageProcessor.process_signature_image(
            original_image_path, 
            processed_image_path, 
            scale_factor=scale_factor,
            quality=image_quality
        )

        p12_data = await p12_file.read()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(PDFSigner.dtr_sign_pdf_sync_owner, input_path, output_path, processed_image_path, p12_data, p12_password,
                                     whole_month)
            future.result()

        # Clean up temp files
        os.remove(input_path)
        os.remove(original_image_path)
        os.remove(processed_image_path)

        return FileResponse(output_path, media_type='application/pdf', filename=output_pdf)

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail="Permission denied: " + str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sign-dtr-incharge/")
async def sign_dtr_incharge(
        input_pdf: UploadFile = File(...),
        p12_file: UploadFile = File(...),
        p12_password: str = Form(...),
        image: UploadFile = File(...),
        whole_month: bool = Form(...),
        scale_factor: float = Form(0.9),  # 0.9 = 90% of original size (10% reduction)
        image_quality: int = Form(100),    # 100% quality
        token: dict = Depends(verify_token),
):
    """
    Sign a DTR (Daily Time Record) PDF as an in-charge person with a digital signature.

    Parameters:
        input_pdf (UploadFile): The PDF file to be signed
        p12_file (UploadFile): The P12/PFX certificate file for digital signing
        p12_password (str): Password for the P12/PFX certificate
        image (UploadFile): Signature image file (PNG format recommended)
        whole_month (bool): Whether to sign for the whole month or specific dates
        scale_factor (float): Scaling factor for the signature image (default: 0.9)
        image_quality (int): Quality of the processed signature image (default: 100)
        token (dict): Authentication token (automatically injected by dependency)

    Returns:
        FileResponse: The signed PDF file

    Raises:
        HTTPException: 
            - 404: If required files are not found
            - 403: If permission is denied
            - 500: For other processing errors
    """
    try:
        # Generate unique filenames with timestamp
        timestamp = int(datetime.datetime.now().timestamp())
        output_pdf = f"signed_incharge_{timestamp}.pdf"
        input_path = os.path.join(TEMP_FILE_DIR, f"input_{timestamp}.pdf")
        output_path = os.path.join(OUTPUT_DIR, output_pdf)
        
        # Image paths
        original_image_path = os.path.join(TEMP_FILE_DIR, f"original_image_{timestamp}.png")
        processed_image_path = os.path.join(TEMP_FILE_DIR, f"processed_image_{timestamp}.png")

        # Save uploaded files to temp directory
        with open(input_path, "wb") as f:
            f.write(await input_pdf.read())

        with open(original_image_path, "wb") as f:
            f.write(await image.read())

        # Process the image
        ImageProcessor.process_signature_image(
            original_image_path, 
            processed_image_path, 
            scale_factor=scale_factor,
            quality=image_quality
        )

        p12_data = await p12_file.read()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(PDFSigner.dtr_sign_pdf_sync_incharge, input_path, output_path, processed_image_path, p12_data, p12_password,
                                     whole_month)
            future.result()

        # Clean up temp files
        os.remove(input_path)
        os.remove(original_image_path)
        os.remove(processed_image_path)

        return FileResponse(output_path, media_type='application/pdf', filename=output_pdf)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail="Permission denied: " + str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sign-leave-application-owner/")
async def sign_leave_application_owner(
        input_pdf: UploadFile = File(...),
        p12_file: UploadFile = File(...),
        p12_password: str = Form(...),
        image: UploadFile = File(...),
        scale_factor: float = Form(0.9),  # 0.9 = 90% of original size (10% reduction)
        image_quality: int = Form(100),    # 100% quality
        # token: dict = Depends(verify_token),
):
    try:
        # Generate unique filename with timestamp
        timestamp = int(datetime.datetime.now().timestamp())
        output_pdf = f"signed_leave_{timestamp}.pdf"
        input_path = os.path.join(TEMP_FILE_DIR, f"input_{timestamp}.pdf")
        output_path = os.path.join(OUTPUT_DIR, output_pdf)

        # Image paths
        original_image_path = os.path.join(TEMP_FILE_DIR, f"image_{timestamp}.png")
        processed_image_path = os.path.join(TEMP_FILE_DIR, f"processed_image_{timestamp}.png")

        # Save uploaded files to temp directory
        with open(input_path, "wb") as f:
            f.write(await input_pdf.read())
        
        with open(original_image_path, "wb") as f:
            f.write(await image.read())

        # Process the image
        ImageProcessor.process_signature_image(
            original_image_path,
            processed_image_path,
            scale_factor=scale_factor,
            quality=image_quality
        )

        p12_data = await p12_file.read()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            pdf_signer = PDFSigner()
            future = executor.submit(pdf_signer.leave_application_sign_pdf_sync_owner, input_path, output_path, processed_image_path, p12_data, p12_password)
            future.result()

        # Clean up temp files
        os.remove(input_path)
        os.remove(original_image_path)
        os.remove(processed_image_path)

        return FileResponse(output_path, media_type='application/pdf', filename=output_pdf)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail="Permission denied: " + str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sign-dtr/")
async def sign_dtr_owner_and_incharge(
    input_pdf: UploadFile = File(...),
    owner_p12_file: UploadFile = File(...),
    owner_p12_password: str = Form(...),
    owner_image: UploadFile = File(...),
    incharge_p12_file: UploadFile = File(...),
    incharge_p12_password: str = Form(...),
    incharge_image: UploadFile = File(...),
    whole_month: bool = Form(...),
    scale_factor: float = Form(0.9),
    image_quality: int = Form(100),
    token: dict = Depends(verify_token),
):
    try:
        timestamp = int(datetime.datetime.now().timestamp())
        output_pdf = f"signed_owner_incharge_{timestamp}.pdf"
        input_path = os.path.join(TEMP_FILE_DIR, f"input_{timestamp}.pdf")
        intermediate_path = os.path.join(TEMP_FILE_DIR, f"intermediate_{timestamp}.pdf")
        output_path = os.path.join(OUTPUT_DIR, output_pdf)

        owner_image_path = os.path.join(TEMP_FILE_DIR, f"owner_image_{timestamp}.png")
        incharge_image_path = os.path.join(TEMP_FILE_DIR, f"incharge_image_{timestamp}.png")

        with open(input_path, "wb") as f:
            f.write(await input_pdf.read())

        with open(owner_image_path, "wb") as f:
            f.write(await owner_image.read())

        with open(incharge_image_path, "wb") as f:
            f.write(await incharge_image.read())

        owner_p12_data = await owner_p12_file.read()
        incharge_p12_data = await incharge_p12_file.read()

        pdf_signer = PDFSigner()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                pdf_signer.dtr_sign_pdf_sync_owner,
                input_path,
                intermediate_path,
                owner_image_path,
                owner_p12_data,
                owner_p12_password,
                whole_month
            )
            future.result()

            future = executor.submit(
                pdf_signer.dtr_sign_pdf_sync_incharge,
                intermediate_path,
                output_path,
                incharge_image_path,
                incharge_p12_data,
                incharge_p12_password,
                whole_month
            )
            future.result()

        os.remove(input_path)
        os.remove(intermediate_path)
        os.remove(owner_image_path)
        os.remove(incharge_image_path)

        return FileResponse(output_path, media_type='application/pdf', filename=output_pdf)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail="Permission denied: " + str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sign-leave-application-head/")
async def sign_leave_application_head(
        input_pdf: UploadFile = File(...),
        p12_file: UploadFile = File(...),
        p12_password: str = Form(...),
        image: UploadFile = File(...),
        scale_factor: float = Form(0.9),  # 0.9 = 90% of original size (10% reduction)
        image_quality: int = Form(100),    # 100% quality
        # token: dict = Depends(verify_token),
):
    try:
        # Generate unique filename with timestamp
        timestamp = int(datetime.datetime.now().timestamp())
        output_pdf = f"head_signed_leave_{timestamp}.pdf"
        input_path = os.path.join(TEMP_FILE_DIR, f"input_{timestamp}.pdf")
        output_path = os.path.join(OUTPUT_DIR, output_pdf)

        # Image paths
        original_image_path = os.path.join(TEMP_FILE_DIR, f"image_{timestamp}.png")
        processed_image_path = os.path.join(TEMP_FILE_DIR, f"processed_image_{timestamp}.png")

        # Save uploaded files to temp directory
        with open(input_path, "wb") as f:
            f.write(await input_pdf.read())
        
        with open(original_image_path, "wb") as f:
            f.write(await image.read())

        # Process the image
        ImageProcessor.process_signature_image(
            original_image_path,
            processed_image_path,
            scale_factor=scale_factor,
            quality=image_quality
        )

        p12_data = await p12_file.read()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            pdf_signer = PDFSigner()
            future = executor.submit(pdf_signer.leave_application_sign_pdf_sync_head, input_path, output_path, processed_image_path, p12_data, p12_password)
            future.result()

        # Clean up temp files
        os.remove(input_path)
        os.remove(original_image_path)
        os.remove(processed_image_path)

        return FileResponse(output_path, media_type='application/pdf', filename=output_pdf)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail="Permission denied: " + str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sign-leave-application-sao/")
async def sign_leave_application_sao(
        input_pdf: UploadFile = File(...),
        p12_file: UploadFile = File(...),
        p12_password: str = Form(...),
        image: UploadFile = File(...),
        scale_factor: float = Form(0.9),  # 0.9 = 90% of original size (10% reduction)
        image_quality: int = Form(100),    # 100% quality
        # token: dict = Depends(verify_token),
):
    try:
        # Generate unique filename with timestamp
        timestamp = int(datetime.datetime.now().timestamp())
        output_pdf = f"sao_signed_leave_{timestamp}.pdf"
        input_path = os.path.join(TEMP_FILE_DIR, f"input_{timestamp}.pdf")
        output_path = os.path.join(OUTPUT_DIR, output_pdf)

        # Image paths
        original_image_path = os.path.join(TEMP_FILE_DIR, f"image_{timestamp}.png")
        processed_image_path = os.path.join(TEMP_FILE_DIR, f"processed_image_{timestamp}.png")

        # Save uploaded files to temp directory
        with open(input_path, "wb") as f:
            f.write(await input_pdf.read())
        
        with open(original_image_path, "wb") as f:
            f.write(await image.read())

        # Process the image
        ImageProcessor.process_signature_image(
            original_image_path,
            processed_image_path,
            scale_factor=scale_factor,
            quality=image_quality
        )

        p12_data = await p12_file.read()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            pdf_signer = PDFSigner()
            future = executor.submit(pdf_signer.leave_application_sign_pdf_sync_sao, input_path, output_path, processed_image_path, p12_data, p12_password)
            future.result()

        # Clean up temp files
        os.remove(input_path)
        os.remove(original_image_path)
        os.remove(processed_image_path)

        return FileResponse(output_path, media_type='application/pdf', filename=output_pdf)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail="Permission denied: " + str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sign-leave-application-cao/")
async def sign_leave_application_cao(
        input_pdf: UploadFile = File(...),
        p12_file: UploadFile = File(...),
        p12_password: str = Form(...),
        image: UploadFile = File(...),
        scale_factor: float = Form(0.9),  # 0.9 = 90% of original size (10% reduction)
        image_quality: int = Form(100),    # 100% quality
        # token: dict = Depends(verify_token),
):
    try:
        # Generate unique filename with timestamp
        timestamp = int(datetime.datetime.now().timestamp())
        output_pdf = f"cao_signed_leave_{timestamp}.pdf"
        input_path = os.path.join(TEMP_FILE_DIR, f"input_{timestamp}.pdf")
        output_path = os.path.join(OUTPUT_DIR, output_pdf)

        # Image paths
        original_image_path = os.path.join(TEMP_FILE_DIR, f"image_{timestamp}.png")
        processed_image_path = os.path.join(TEMP_FILE_DIR, f"processed_image_{timestamp}.png")

        # Save uploaded files to temp directory
        with open(input_path, "wb") as f:
            f.write(await input_pdf.read())
        
        with open(original_image_path, "wb") as f:
            f.write(await image.read())

        # Process the image
        ImageProcessor.process_signature_image(
            original_image_path,
            processed_image_path,
            scale_factor=scale_factor,
            quality=image_quality
        )

        p12_data = await p12_file.read()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            pdf_signer = PDFSigner()
            future = executor.submit(pdf_signer.leave_application_sign_pdf_sync_cao, input_path, output_path, processed_image_path, p12_data, p12_password)
            future.result()

        # Clean up temp files
        os.remove(input_path)
        os.remove(original_image_path)
        os.remove(processed_image_path)

        return FileResponse(output_path, media_type='application/pdf', filename=output_pdf)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail="Permission denied: " + str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
