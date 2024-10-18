from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from pyhanko import stamp
from pyhanko.pdf_utils.images import PdfImage
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import fields, signers
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from fastapi.responses import FileResponse
import os
import concurrent.futures

app = FastAPI()


def extract_cert_and_key(p12_data: bytes, p12_password: str):
    # Load the PKCS#12 file from bytes
    private_key, certificate, additional_certificates = load_key_and_certificates(
        p12_data,
        p12_password.encode()
    )

    # Write the certificate and key to PEM format
    cert_pem = certificate.public_bytes(Encoding.PEM)
    key_pem = private_key.private_bytes(
        Encoding.PEM,
        PrivateFormat.PKCS8,
        NoEncryption()
    )

    # Write to temporary files
    cert_path = "temp_cert.pem"
    key_path = "temp_key.pem"
    with open(cert_path, "wb") as cert_file:
        cert_file.write(cert_pem)
    with open(key_path, "wb") as key_file:
        key_file.write(key_pem)

    return cert_path, key_path

def sign_pdf_sync(input_path: str, output_path: str, image_path: str, p12_data: bytes, p12_password: str):
    # Extract cert and key from p12 file data
    cert_path, key_path = extract_cert_and_key(p12_data, p12_password)

    # Load signer using extracted cert and key
    signer = signers.SimpleSigner.load(key_path, cert_path)
    pdf_image = PdfImage(image_path)

    # First signature
    with open(input_path, 'rb') as inf:
        w = IncrementalPdfFileWriter(inf)
        fields.append_signature_field(w, sig_field_spec=fields.SigFieldSpec(
            'Signature1',
            box=(50, 115, 250, 175) # box-dimension: w = 200, h = 60
        ))
        meta = signers.PdfSignatureMetadata(field_name='Signature1')
        pdf_signer = signers.PdfSigner(meta, signer=signer, stamp_style=stamp.TextStampStyle(
            stamp_text='\n\n\nSigned by: %(signer)s\nTime: %(ts)s',
            background=pdf_image,
            border_width=0
        ))

        # Save intermediate signed PDF with the first signature
        intermediate_output = "intermediate_output.pdf"
        with open(intermediate_output, 'wb') as outf:
            pdf_signer.sign_pdf(w, output=outf)

    # Second signature
    with open(intermediate_output, 'rb') as inf:
        w = IncrementalPdfFileWriter(inf)
        fields.append_signature_field(w, sig_field_spec=fields.SigFieldSpec(
            'Signature2',
            box=(360, 115, 560, 175) # box-dimension: w = 200, h = 60
        ))
        meta = signers.PdfSignatureMetadata(field_name='Signature2')
        pdf_signer = signers.PdfSigner(meta, signer=signer, stamp_style=stamp.TextStampStyle(
            stamp_text='\n\n\nSigned by: %(signer)s\nTime: %(ts)s',
            background=pdf_image,
            border_width=0
        ))

        # Save the final output with both signatures
        with open(output_path, 'wb') as outf:
            pdf_signer.sign_pdf(w, output=outf)

    # Clean up temporary files
    os.remove(cert_path)
    os.remove(key_path)
    os.remove(intermediate_output)


@app.post("/sign-dtr/")
async def sign_dtr(
        input_pdf: UploadFile = File(...),
        p12_file: UploadFile = File(...),
        image: UploadFile = File(...),
        output_filename: str = Form(...),
        p12_password: str = Form(...)
):
    try:
        # Save uploaded files temporarily
        input_path = f"{input_pdf.filename}"
        output_path = f"{output_filename}"
        image_path = f"{image.filename}"

        with open(input_path, "wb") as f:
            f.write(await input_pdf.read())

        with open(image_path, "wb") as f:
            f.write(await image.read())

        p12_data = await p12_file.read()

        # Run the PDF signing process in a synchronous thread
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(sign_pdf_sync, input_path, output_path, image_path, p12_data, p12_password)
            future.result()  # Wait for completion

        return FileResponse(output_path, media_type='application/pdf', filename=output_filename)

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail="Permission denied: " + str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
