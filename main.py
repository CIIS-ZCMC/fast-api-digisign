import concurrent.futures
import os
import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import FileResponse
from app.utils.auth import verify_token
from app.services.pdf_signer import PDFSigner
from app.utils.image_processor import ImageProcessor
from app.core.config import TEMP_FILE_DIR, OUTPUT_DIR

app = FastAPI()

@app.post("/sign-dtr-owner/")
async def sign_dtr_owner(
        input_pdf: UploadFile = File(...),
        p12_file: UploadFile = File(...),
        p12_password: str = Form(...),
        image: UploadFile = File(...),
        whole_month: bool = Form(...),
        scale_factor: float = Form(0.9),  # 0.9 = 90% of original size (10% reduction)
        image_quality: int = Form(100),    # 95% quality
        token: dict = Depends(verify_token),
):
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
            future = executor.submit(PDFSigner.sign_pdf_sync_owner, input_path, output_path, processed_image_path, p12_data, p12_password,
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
        image_quality: int = Form(100),    # 95% quality
        token: dict = Depends(verify_token),
):
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
            future = executor.submit(PDFSigner.sign_pdf_sync_incharge, input_path, output_path, processed_image_path, p12_data, p12_password,
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
