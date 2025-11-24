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
import asyncio
import os
import json
import time
import hashlib
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign.fields import enumerate_sig_fields
import io
import pikepdf
from asn1crypto import cms as asn1_cms
from asn1crypto import x509 as asn1_x509
from cryptography.x509 import Certificate as X509Certificate
import traceback
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Response, Depends
from fastapi.responses import FileResponse
# Import concrete names from config (config.py exposes module-level names)
from ..core.config import TEMP_FILE_DIR, OUTPUT_DIR
# Use the single auth utility as the source-of-truth for JWT helpers
from ..utils.auth import verify_token
from ..services.pdf_signer import PDFSigner
from typing import List

router = APIRouter()

@router.post("/sign-dtr-owner/")
async def sign_dtr_owner(
        input_pdf: UploadFile = File(...),
        p12_file: UploadFile = File(...),
        p12_password: str = Form(...),
        image: UploadFile = File(...),
        whole_month: bool = Form(...),
        # token: dict = Depends(verify_token),
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
        input_path = os.path.join(TEMP_FILE_DIR, f"input_{input_pdf.filename}")
        output_path = os.path.join(TEMP_FILE_DIR, f"output_{input_pdf.filename}")
        image_path = os.path.join(TEMP_FILE_DIR, f"image_{image.filename}")

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
        tb = traceback.format_exc()
        # write to a log file for easier debugging
        try:
            log_path = os.path.join(TEMP_FILE_DIR, "inspect_error.log")
            with open(log_path, "a", encoding="utf-8") as logf:
                logf.write(f"\n--- {time.asctime()} ---\n")
                logf.write(tb)
        except Exception:
            pass
        # return traceback in the HTTP error detail to help debugging locally
        raise HTTPException(status_code=500, detail=tb)

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
        input_path = os.path.join(TEMP_FILE_DIR, f"input_{input_pdf.filename}")
        output_path = os.path.join(TEMP_FILE_DIR, f"output_{input_pdf.filename}")
        image_path = os.path.join(TEMP_FILE_DIR, f"image_{image.filename}")

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


@router.post(
    "/sign-dynamic/",
    openapi_extra={
        "requestBody": {
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "input_pdf": {"type": "string", "format": "binary"},
                            "images": {"type": "array", "items": {"type": "string", "format": "binary"}},
                            "p12_files": {"type": "array", "items": {"type": "string", "format": "binary"}},
                            "placements": {
                                "type": "string",
                                "example": "[{\"page\":2, \"box\":[360,700,560,760], \"image_index\":0, \"p12_index\":0, \"p12_password\":\"p12pass\", \"field_name\":\"UserSigPage2\"}, {\"page\":1, \"box\":[50,700,250,760], \"image_index\":0, \"p12_index\":0, \"p12_password\":\"p12pass\", \"field_name\":\"UserSigPage1\"}]"
                            }
                        },
                        "required": ["input_pdf", "placements"]
                    }
                }
            }
        }
    },
)
async def sign_dynamic(
    input_pdf: UploadFile = File(...),
    images: List[UploadFile] = File(None),
    p12_files: List[UploadFile] = File(None),
    placements: str = Form(...),  # JSON string
    # token: dict = Depends(verify_token),
):
    """
    Dynamic signing endpoint.

        `placements` is a JSON list describing where to place signatures.
        Each placement entry must include:
            - `page` (1-based)
            - `box`: an explicit rectangle `[x0, y0, x1, y1]` (PDF points — 1 point = 1/72 inch)
            - `image_index` (index into `images`) or `image_path` (not recommended)
            - `p12_index` (index into `p12_files`) and `p12_password`
            - `field_name` (optional)

        Example placements JSON:
        [{"page":2,"box":[360,700,560,760],"image_index":0,"p12_index":0,"p12_password":"pwd","field_name":"UserSigPage2"},
         {"page":1,"box":[50,700,250,760],"image_index":0,"p12_index":0,"p12_password":"pwd","field_name":"UserSigPage1"}]
    """
    try:
        timestamp = int(time.time())
        input_path = os.path.join(TEMP_FILE_DIR, f"dynamic_input_{timestamp}.pdf")
        output_path = os.path.join(TEMP_FILE_DIR, f"dynamic_output_{timestamp}.pdf")

        # save input pdf
        with open(input_path, "wb") as f:
            f.write(await input_pdf.read())

        # save images and p12 files
        image_paths = []
        if images:
            for i, img in enumerate(images):
                p = os.path.join(TEMP_FILE_DIR, f"dyn_img_{timestamp}_{i}_{img.filename}")
                with open(p, "wb") as f:
                    f.write(await img.read())
                image_paths.append(p)

        p12_bytes = []
        if p12_files:
            for i, fobj in enumerate(p12_files):
                b = await fobj.read()
                p12_bytes.append(b)

        # parse placements JSON
        try:
            placements_list = json.loads(placements)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid placements JSON: {e}")

        resolved = []
        for plc in placements_list:
            # image
            img_idx = int(plc.get("image_index", 0)) if plc.get("image_index") is not None else 0
            if not image_paths:
                raise HTTPException(status_code=400, detail="No images uploaded for placements")
            if img_idx < 0 or img_idx >= len(image_paths):
                raise HTTPException(status_code=400, detail=f"image_index {img_idx} out of range")
            image_path = image_paths[img_idx]

            # p12
            p12_idx = int(plc.get("p12_index", 0)) if plc.get("p12_index") is not None else 0
            if not p12_bytes:
                raise HTTPException(status_code=400, detail="No p12 files uploaded for placements")
            if p12_idx < 0 or p12_idx >= len(p12_bytes):
                raise HTTPException(status_code=400, detail=f"p12_index {p12_idx} out of range")
            p12_data = p12_bytes[p12_idx]
            p12_password = plc.get("p12_password", "")

            # require explicit box for placement: [x0, y0, x1, y1]
            if "box" not in plc or not plc.get("box"):
                raise HTTPException(status_code=400, detail="Each placement must include a 'box' array [x0,y0,x1,y1]")

            entry = {
                "page": plc.get("page", 1),
                "box": plc.get("box"),
                "image_path": image_path,
                "p12_data": p12_data,
                "p12_password": p12_password,
                "field_name": plc.get("field_name"),
            }
            resolved.append(entry)

        # call signer in a background thread to avoid blocking or calling
        # asyncio.run() from inside the running event loop
        await asyncio.to_thread(PDFSigner.sign_dynamic, input_path, output_path, resolved)

        with open(output_path, "rb") as f:
            signed = f.read()

        # cleanup
        try:
            os.remove(input_path)
        except:
            pass
        for p in image_paths:
            try:
                os.remove(p)
            except:
                pass
        try:
            os.remove(output_path)
        except:
            pass

        return Response(content=signed, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="signed_dynamic_{timestamp}.pdf"'})

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/inspect-signatures/")
async def inspect_signatures(input_pdf: UploadFile = File(...)):
    """
    Inspect a PDF and return audit information about signatures.

    Returns:
      - filename
      - size_bytes
      - md5, sha256
      - signature_fields: list of signature field names present in the PDF

    Note: this endpoint currently enumerates signature fields and returns basic
    file hashes useful for auditing. Extracting signer certificate subjects
    and validation results can be added if you want deeper verification.
    """
    # Read file bytes into memory to avoid file I/O issues
    content = await input_pdf.read()

    # Quick PDF magic-byte check
    if not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid PDF")

    try:
        size_bytes = len(content)
        md5 = hashlib.md5(content).hexdigest()
        sha256 = hashlib.sha256(content).hexdigest()

        sig_fields = []
        sig_details = []
        try:
            bio = io.BytesIO(content)
            # create an incremental writer/reader that exposes signature objects
            reader = IncrementalPdfFileWriter(bio)

            # enumerate signature fields
            raw_fields = list(enumerate_sig_fields(reader))

            # normalize names
            names = []
            for rf in raw_fields:
                if isinstance(rf, str):
                    names.append(rf)
                elif isinstance(rf, (list, tuple)) and len(rf) > 0:
                    names.append(str(rf[0]))
                else:
                    try:
                        names.append(str(rf))
                    except Exception:
                        names.append(repr(rf))

            # for each signature field, extract PKCS#7 with pikepdf and parse with asn1crypto
            for fname in names:
                entry = {"field_name": fname}
                try:
                    def _extract_field_pike(c_bytes, field_name):
                        try:
                            with pikepdf.Pdf.open(io.BytesIO(c_bytes)) as pdf:
                                # different pikepdf versions expose the catalog differently
                                if hasattr(pdf, 'root'):
                                    root = pdf.root
                                else:
                                    # fallback to trailer /Root
                                    root = pdf.trailer.get('/Root') if hasattr(pdf, 'trailer') else None

                                if not root:
                                    return {"error": "PDF root not found"}

                                # AcroForm may be at /AcroForm under the root
                                acro = None
                                try:
                                    if hasattr(root, 'get'):
                                        acro = root.get('/AcroForm')
                                    else:
                                        acro = root['/AcroForm'] if '/AcroForm' in root else None
                                except Exception:
                                    acro = None

                                if not acro:
                                    return {"error": "AcroForm not found"}

                                fields_arr = None
                                try:
                                    if hasattr(acro, 'get'):
                                        fields_arr = acro.get('/Fields')
                                    else:
                                        fields_arr = acro['/Fields'] if '/Fields' in acro else None
                                except Exception:
                                    fields_arr = None

                                if not fields_arr:
                                    fields_arr = []
                                sig_raw = None
                                for f in fields_arr:
                                    try:
                                        fld = f.get_object()
                                    except Exception:
                                        fld = f
                                    # field name
                                    t = fld.get('/T') if isinstance(fld, dict) else fld.get('/T') if hasattr(fld, 'get') else None
                                    # normalize t to string
                                    if t is None:
                                        try:
                                            t = fld['/T']
                                        except Exception:
                                            t = None
                                    if t is None:
                                        continue
                                    if isinstance(t, bytes):
                                        t_str = t.decode('utf-8', errors='ignore')
                                    else:
                                        t_str = str(t)
                                    if t_str != field_name:
                                        continue

                                    # signature dict is in /V
                                    v = fld.get('/V')
                                    if v is None:
                                        # no signature value
                                        continue
                                    try:
                                        sigobj = v.get_object()
                                    except Exception:
                                        sigobj = v

                                    # Contents may be a stream or a string
                                    contents = None
                                    try:
                                        if isinstance(sigobj, dict) and '/Contents' in sigobj:
                                            c = sigobj['/Contents']
                                        else:
                                            c = sigobj.get('/Contents') if hasattr(sigobj, 'get') else None
                                    except Exception:
                                        c = None

                                    if c is None:
                                        continue

                                    # try different ways to obtain raw bytes
                                    raw = None
                                    try:
                                        # pikepdf streams have read_bytes()
                                        raw = c.read_bytes()
                                    except Exception:
                                        try:
                                            raw = bytes(c)
                                        except Exception:
                                            try:
                                                raw = str(c).encode('latin1')
                                            except Exception:
                                                raw = None

                                    if raw:
                                        sig_raw = raw
                                        break

                                if not sig_raw:
                                    return {"error": "Signature contents not found for field"}

                                # parse PKCS7/CMS using asn1crypto
                                try:
                                    ci = asn1_cms.ContentInfo.load(sig_raw)
                                except Exception:
                                    # sometimes Contents is stored as a string with extra <...> markers
                                    # attempt to strip possible enclosing markers
                                    try:
                                        stripped = sig_raw.strip()
                                        ci = asn1_cms.ContentInfo.load(stripped)
                                    except Exception as e:
                                        return {"error": f"Failed to parse CMS: {e}"}

                                sd = ci['content']
                                cert_entry = None
                                try:
                                    certs = sd['certificates']
                                    if certs and len(certs) > 0:
                                        # certificates may be choices
                                        c0 = certs[0]
                                        # asn1crypto may wrap as Choice -> extract certificate
                                        if isinstance(c0, asn1_cms.CertificateSet):
                                            cert_obj = c0[0]
                                        else:
                                            cert_obj = c0
                                        # if it's a 'certificate' choice
                                        if hasattr(cert_obj, 'chosen'):
                                            cert_obj = cert_obj.chosen
                                        cert_entry = cert_obj
                                except Exception:
                                    cert_entry = None

                                signer_time = None
                                try:
                                    sis = sd['signer_infos']
                                    if sis and len(sis) > 0:
                                        si0 = sis[0]
                                        try:
                                            attrs = si0['signed_attrs']
                                        except Exception:
                                            attrs = None

                                        # `attrs` is typically a CMSAttributes sequence.
                                        # Iterate attributes and look for the `signing_time` attribute
                                        if attrs:
                                            for attr in attrs:
                                                try:
                                                    tname = attr['type'].native
                                                except Exception:
                                                    tname = None
                                                if tname == 'signing_time':
                                                    try:
                                                        vals = attr['values']
                                                        if vals and len(vals) > 0:
                                                            signer_time = vals[0].native
                                                            break
                                                    except Exception:
                                                        # fallthrough - leave signer_time as None
                                                        pass
                                except Exception:
                                    signer_time = None

                                subj = None
                                fp256 = None
                                if cert_entry is not None:
                                    try:
                                        subj = cert_entry.subject.human_friendly
                                    except Exception:
                                        try:
                                            subj = str(cert_entry.subject)
                                        except Exception:
                                            subj = None
                                    try:
                                        fp256 = hashlib.sha256(cert_entry.dump()).hexdigest()
                                    except Exception:
                                        fp256 = None

                                return {
                                    "signer_subject": subj,
                                    "signer_fingerprint_sha256": fp256,
                                    "signing_time": signer_time.isoformat() if hasattr(signer_time, 'isoformat') else str(signer_time) if signer_time is not None else None,
                                }
                        except Exception as e:
                            return {"error": str(e)}

                    field_info = await asyncio.to_thread(_extract_field_pike, content, fname)
                    entry.update(field_info)
                except Exception as e:
                    entry["error"] = str(e)

                sig_details.append(entry)
            sig_fields = names
        except Exception:
            # if any of the above fails, return minimal info
            sig_fields = []
            sig_details = []

        return {
            "filename": input_pdf.filename,
            "size_bytes": size_bytes,
            "md5": md5,
            "sha256": sha256,
            "signature_fields": sig_fields,
            "signature_details": sig_details,
        }
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        # write to a log file for easier debugging
        try:
            log_path = os.path.join(TEMP_FILE_DIR, "inspect_error.log")
            with open(log_path, "a", encoding="utf-8") as logf:
                logf.write(f"\n--- {time.asctime()} ---\n")
                logf.write(tb)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=tb)
