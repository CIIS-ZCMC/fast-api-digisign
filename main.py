import concurrent.futures
import os

from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pyhanko import stamp
from pyhanko.pdf_utils.images import PdfImage
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import fields, signers
from pyhanko.sign.fields import enumerate_sig_fields

app = FastAPI()

def extract_cert_and_key(p12_data: bytes, p12_password: str):
    private_key, certificate, additional_certificates = load_key_and_certificates(
        p12_data,
        p12_password.encode()
    )
    cert_pem = certificate.public_bytes(Encoding.PEM)
    key_pem = private_key.private_bytes(
        Encoding.PEM,
        PrivateFormat.PKCS8,
        NoEncryption()
    )

    cert_path = "temp_cert.pem"
    key_path = "temp_key.pem"
    with open(cert_path, "wb") as cert_file:
        cert_file.write(cert_pem)
    with open(key_path, "wb") as key_file:
        key_file.write(key_pem)

    return cert_path, key_path

def sign_pdf_sync_incharge(input_path: str, output_path: str, image_path: str, p12_data: bytes, p12_password: str,
                           whole_month: bool):
    cert_path, key_path = extract_cert_and_key(p12_data, p12_password)
    signer = signers.SimpleSigner.load(key_path, cert_path)
    pdf_image = PdfImage(image_path)

    # Load existing PDF
    with open(input_path, 'rb') as inf:
        w = IncrementalPdfFileWriter(inf)

        # Check if 'InchargeSignature1' already exists
        field_exists = 'InchargeSignature1' in enumerate_sig_fields(w)

        if not field_exists:
            # Add the first signature field if it does not exist
            fields.append_signature_field(w, sig_field_spec=fields.SigFieldSpec(
                'InchargeSignature1',
                box=(50, 80, 250, 140)
            ))

        meta = signers.PdfSignatureMetadata(field_name='InchargeSignature1')
        pdf_signer = signers.PdfSigner(meta, signer=signer, stamp_style=stamp.TextStampStyle(
            stamp_text='\n\n\nSigned by: %(signer)s\nTime: %(ts)s',
            background=pdf_image,
            border_width=0
        ))

        intermediate_output = "intermediate_output.pdf"
        with open(intermediate_output, 'wb') as outf:
            pdf_signer.sign_pdf(w, output=outf)

    # Add second signature
    with open(intermediate_output, 'rb') as inf:
        w = IncrementalPdfFileWriter(inf)
        fields.append_signature_field(w, sig_field_spec=fields.SigFieldSpec(
            'InchargeSignature2',
            box=(360, 80, 560, 140)
        ))
        meta = signers.PdfSignatureMetadata(field_name='InchargeSignature2')
        pdf_signer = signers.PdfSigner(meta, signer=signer, stamp_style=stamp.TextStampStyle(
            stamp_text='\n\n\nSigned by: %(signer)s\nTime: %(ts)s',
            background=pdf_image,
            border_width=0
        ))

        with open(output_path, 'wb') as outf:
            pdf_signer.sign_pdf(w, output=outf)

    os.remove(cert_path)
    os.remove(key_path)
    os.remove(intermediate_output)

def sign_pdf_sync_owner(input_path: str, output_path: str, image_path: str, p12_data: bytes, p12_password: str,
                        whole_month: bool):
    cert_path, key_path = extract_cert_and_key(p12_data, p12_password)
    signer = signers.SimpleSigner.load(key_path, cert_path)
    pdf_image = PdfImage(image_path)

    with open(input_path, 'rb') as inf:
        w = IncrementalPdfFileWriter(inf)
        fields.append_signature_field(w, sig_field_spec=fields.SigFieldSpec(
            'OwnerSignature1',
            box=(50, 115, 250, 175)
        ))
        meta = signers.PdfSignatureMetadata(field_name='OwnerSignature1')
        pdf_signer = signers.PdfSigner(meta, signer=signer, stamp_style=stamp.TextStampStyle(
            stamp_text='\n\n\nSigned by: %(signer)s\nTime: %(ts)s',
            background=pdf_image,
            border_width=0
        ))

        intermediate_output = "intermediate_output.pdf"
        with open(intermediate_output, 'wb') as outf:
            pdf_signer.sign_pdf(w, output=outf)

    with open(intermediate_output, 'rb') as inf:
        w = IncrementalPdfFileWriter(inf)
        fields.append_signature_field(w, sig_field_spec=fields.SigFieldSpec(
            'OwnerSignature2',
            box=(360, 115, 560, 175)
        ))
        meta = signers.PdfSignatureMetadata(field_name='OwnerSignature2')
        pdf_signer = signers.PdfSigner(meta, signer=signer, stamp_style=stamp.TextStampStyle(
            stamp_text='\n\n\nSigned by: %(signer)s\nTime: %(ts)s',
            background=pdf_image,
            border_width=0
        ))

        with open(output_path, 'wb') as outf:
            pdf_signer.sign_pdf(w, output=outf)

    os.remove(cert_path)
    os.remove(key_path)
    os.remove(intermediate_output)

@app.post("/sign-dtr-owner/")
async def sign_dtr_owner(
        input_pdf: UploadFile = File(...),
        p12_file: UploadFile = File(...),
        p12_password: str = Form(...),
        image: UploadFile = File(...),
        whole_month: bool = Form(...)
):
    try:
        output_pdf = "signed_owner.pdf"
        input_path = f"{input_pdf.filename}"
        output_path = f"{output_pdf}"
        image_path = f"{image.filename}"

        with open(input_path, "wb") as f:
            f.write(await input_pdf.read())

        with open(image_path, "wb") as f:
            f.write(await image.read())

        p12_data = await p12_file.read()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(sign_pdf_sync_owner, input_path, output_path, image_path, p12_data, p12_password,
                                     whole_month)
            future.result()

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
        whole_month: bool = Form(...)
):
    try:
        output_pdf = "signed_incharge.pdf"
        input_path = f"{input_pdf.filename}"
        output_path = f"{output_pdf}"
        image_path = f"{image.filename}"

        with open(input_path, "wb") as f:
            f.write(await input_pdf.read())

        with open(image_path, "wb") as f:
            f.write(await image.read())

        p12_data = await p12_file.read()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(sign_pdf_sync_incharge, input_path, output_path, image_path, p12_data, p12_password,
                                     whole_month)
            future.result()

        return FileResponse(output_path, media_type='application/pdf', filename=output_pdf)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail="Permission denied: " + str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
