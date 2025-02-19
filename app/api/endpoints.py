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
                    PDFSigner.sign_pdf_sync_owner,
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
                    PDFSigner.sign_pdf_sync_incharge,
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
