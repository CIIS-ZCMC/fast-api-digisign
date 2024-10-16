from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pyhanko import stamp
from pyhanko.pdf_utils.images import PdfImage
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import fields, signers
import os
import concurrent.futures

# Database URL (update this with your actual password and database name)
DATABASE_URL = "mysql+aiomysql://root:@localhost:3306/user_management_den"
app = FastAPI()

class PDFSignRequest(BaseModel):
    input_path: str
    output_path: str
    image_path: str

def sign_pdf_sync(input_path: str, output_path: str, image_path: str):
    # Load signer and image
    signer = signers.SimpleSigner.load('key.pem', 'cert.pem')
    pdf_image = PdfImage(image_path)

    with open(input_path, 'rb') as inf:
        w = IncrementalPdfFileWriter(inf)
        fields.append_signature_field(w, sig_field_spec=fields.SigFieldSpec('Signature', box=(200, 600, 400, 660)))
        meta = signers.PdfSignatureMetadata(field_name='Signature')
        pdf_signer = signers.PdfSigner(meta, signer=signer, stamp_style=stamp.TextStampStyle(
            stamp_text='\n\n\nDigitally Signed by: %(signer)s\nTime: %(ts)s',
            background=pdf_image,
            border_width=0
        ))

        with open(output_path, 'wb') as outf:
            pdf_signer.sign_pdf(w, output=outf)

@app.post("/sign-pdf/")
async def sign_pdf(request: PDFSignRequest):
    try:
        # Ensure all file paths exist
        if not os.path.isfile(request.input_path) or not os.path.isfile(request.image_path):
            raise HTTPException(status_code=404, detail="Input or image file not found")

        # Run the PDF signing process in a synchronous thread
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(sign_pdf_sync, request.input_path, request.output_path, request.image_path)
            future.result()  # Wait for completion

        return {"message": "PDF signed successfully", "output_path": request.output_path}

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail="Permission denied: " + str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
