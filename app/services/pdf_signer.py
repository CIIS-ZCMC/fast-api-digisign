"""
PDF Digital Signature Service

This module provides functionality for digitally signing PDF documents using digital certificates
and signature images. It supports both owner and in-charge signature placements with specific
positioning and styling.

The service uses pyhanko for PDF manipulation and cryptography for certificate handling.
It implements a two-signature system where each document can be signed twice in different
positions, useful for multi-page or multi-signature requirements.
"""

import os
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from pyhanko import stamp
from pyhanko.pdf_utils.images import PdfImage
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import fields, signers
from pyhanko.sign.fields import enumerate_sig_fields

class PDFSigner:
    """
    A utility class for handling PDF digital signatures.
    
    This class provides static methods for extracting certificates and signing PDFs
    with digital signatures and visual stamps. It supports both owner and in-charge
    signature placements with specific positioning.
    """

    @staticmethod
    def extract_cert_and_key(p12_data: bytes, p12_password: str) -> tuple[str, str]:
        """
        Extract certificate and private key from P12/PFX data.

        Args:
            p12_data (bytes): Raw P12/PFX certificate data
            p12_password (str): Password to decrypt the P12/PFX data

        Returns:
            tuple[str, str]: Paths to the temporary certificate and key PEM files

        Note:
            This method creates temporary files that should be cleaned up after use
        """
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

    @staticmethod
    def dtr_sign_pdf_sync_owner(input_path: str, output_path: str, image_path: str, p12_data: bytes, p12_password: str,
                           whole_month: bool) -> None:
        """
        Sign a PDF as an owner with two signature fields.

        This method adds two signature fields to the PDF:
        1. OwnerSignature1: Positioned at (50, 105, 250, 165)
        2. OwnerSignature2: Positioned at (360, 105, 560, 165)

        Args:
            input_path (str): Path to the input PDF file
            output_path (str): Path where the signed PDF will be saved
            image_path (str): Path to the signature image file
            p12_data (bytes): Raw P12/PFX certificate data
            p12_password (str): Password to decrypt the P12/PFX data
            whole_month (bool): Flag indicating if signing for whole month

        Note:
            The method creates and cleans up temporary files during execution
        """
        cert_path, key_path = PDFSigner.extract_cert_and_key(p12_data, p12_password)
        signer = signers.SimpleSigner.load(key_path, cert_path)
        pdf_image = PdfImage(image_path)

        adjust_y = 0 if whole_month else 250 

        with open(input_path, 'rb') as inf:
            w = IncrementalPdfFileWriter(inf)
            fields.append_signature_field(w, sig_field_spec=fields.SigFieldSpec(
                'OwnerSignature1',
                box=(50, 105 + adjust_y, 250, 165 + adjust_y)
            ))
            meta = signers.PdfSignatureMetadata(field_name='OwnerSignature1')
            pdf_signer = signers.PdfSigner(meta, signer=signer, stamp_style=stamp.TextStampStyle(
                stamp_text='\n\n\nSigned by: %(signer)s\nDate Signed: %(ts)s',
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
                box=(360, 105 + adjust_y, 560, 165 + adjust_y)
            ))
            meta = signers.PdfSignatureMetadata(field_name='OwnerSignature2')
            pdf_signer = signers.PdfSigner(meta, signer=signer, stamp_style=stamp.TextStampStyle(
                stamp_text='\n\n\nSigned by: %(signer)s\nDate Signed: %(ts)s',
                background=pdf_image,
                border_width=0
            ))

            with open(output_path, 'wb') as outf:
                pdf_signer.sign_pdf(w, output=outf)

        os.remove(cert_path)
        os.remove(key_path)
        os.remove(intermediate_output)

    @staticmethod
    def dtr_sign_pdf_sync_incharge(input_path: str, output_path: str, image_path: str, p12_data: bytes, p12_password: str,
                              whole_month: bool) -> None:
        """
        Sign a PDF as an in-charge person with two signature fields.

        This method adds two signature fields to the PDF:
        1. InchargeSignature1: Positioned at (50, 70, 250, 130)
        2. InchargeSignature2: Positioned at (360, 70, 560, 130)

        Args:
            input_path (str): Path to the input PDF file
            output_path (str): Path where the signed PDF will be saved
            image_path (str): Path to the signature image file
            p12_data (bytes): Raw P12/PFX certificate data
            p12_password (str): Password to decrypt the P12/PFX data
            whole_month (bool): Flag indicating if signing for whole month

        Note:
            The method creates and cleans up temporary files during execution
        """
        cert_path, key_path = PDFSigner.extract_cert_and_key(p12_data, p12_password)
        signer = signers.SimpleSigner.load(key_path, cert_path)
        pdf_image = PdfImage(image_path)

        adjust_y = 0 if whole_month else 255 

        # Load existing PDF
        with open(input_path, 'rb') as inf:
            w = IncrementalPdfFileWriter(inf)

            # Check if 'InchargeSignature1' already exists
            field_exists = 'InchargeSignature1' in enumerate_sig_fields(w)

            if not field_exists:
                # Add the first signature field if it does not exist
                fields.append_signature_field(w, sig_field_spec=fields.SigFieldSpec(
                    'InchargeSignature1',
                    box=(50, 70 + adjust_y, 250, 130 + adjust_y)
                ))

            meta = signers.PdfSignatureMetadata(field_name='InchargeSignature1')
            pdf_signer = signers.PdfSigner(meta, signer=signer, stamp_style=stamp.TextStampStyle(
                stamp_text='\n\n\nSigned by: %(signer)s\nDate Signed: %(ts)s',
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
                box=(360, 70 + adjust_y, 560, 130 + adjust_y)
            ))
            meta = signers.PdfSignatureMetadata(field_name='InchargeSignature2')
            pdf_signer = signers.PdfSigner(meta, signer=signer, stamp_style=stamp.TextStampStyle(
                stamp_text='\n\n\nSigned by: %(signer)s\nDate Signed: %(ts)s',
                background=pdf_image,
                border_width=0
            ))

            with open(output_path, 'wb') as outf:
                pdf_signer.sign_pdf(w, output=outf)

        os.remove(cert_path)
        os.remove(key_path)
        os.remove(intermediate_output)


    def leave_application_sign_pdf_sync_owner(self, input_path: str, output_path: str, image_path: str, p12_data: bytes, p12_password: str) -> None:
        cert_path, key_path = PDFSigner.extract_cert_and_key(p12_data, p12_password)
        signer = signers.SimpleSigner.load(key_path, cert_path)
        pdf_image =PdfImage(image_path)

        x = 330
        y = 535 
        x2 = x + 220
        y2 = y + 70
        
        with open(input_path, 'rb') as inf:
            w = IncrementalPdfFileWriter(inf)
            fields.append_signature_field(w, sig_field_spec=fields.SigFieldSpec(
                'OwnerSignature2',
                box=(x, y, x2, y2)
            ))
            meta = signers.PdfSignatureMetadata(field_name='OwnerSignature2')
            pdf_signer = signers.PdfSigner(meta, signer=signer, stamp_style=stamp.TextStampStyle(
                stamp_text='\n\n\nSigned by: %(signer)s\nDate Signed: %(ts)s',
                background=pdf_image,
                border_width=0
            ))

            with open(output_path, 'wb') as outf:
                pdf_signer.sign_pdf(w, output=outf)

        os.remove(cert_path)
        os.remove(key_path)
        # os.remove(intermediate_output)

    def leave_application_sign_pdf_sync_head(self, input_path: str, output_path: str, image_path: str, p12_data: bytes, p12_password: str) -> None:
        cert_path, key_path = PDFSigner.extract_cert_and_key(p12_data, p12_password)
        signer = signers.SimpleSigner.load(key_path, cert_path)
        pdf_image = PdfImage(image_path)

        x = 330  # Position for CAO signature
        y = 355  # increase the value to move up
        x2 = x + 220
        y2 = y + 70


        with open(input_path, 'rb') as inf:
            w = IncrementalPdfFileWriter(inf)
            fields.append_signature_field(w, sig_field_spec=fields.SigFieldSpec(
                'HeadSignature2',
                box=(x, y, x2, y2)
            ))
            meta = signers.PdfSignatureMetadata(field_name='HeadSignature2')
            pdf_signer = signers.PdfSigner(meta, signer=signer, stamp_style=stamp.TextStampStyle(
                stamp_text='\n\n\nSigned by: %(signer)s\nDate Signed: %(ts)s',
                background=pdf_image,
                border_width=0
            ))

            with open(output_path, 'wb') as outf:
                pdf_signer.sign_pdf(w, output=outf)

        os.remove(cert_path)
        os.remove(key_path)

    def leave_application_sign_pdf_sync_sao(self, input_path: str, output_path: str, image_path: str, p12_data: bytes, p12_password: str) -> None:
        cert_path, key_path = PDFSigner.extract_cert_and_key(p12_data, p12_password)
        signer = signers.SimpleSigner.load(key_path, cert_path)
        pdf_image = PdfImage(image_path)

        x = 50  # move x axis | left: decrease | right: increase
        y = 355  # increase the value to move up
        x2 = x + 220
        y2 = y + 70


        with open(input_path, 'rb') as inf:
            w = IncrementalPdfFileWriter(inf)
            fields.append_signature_field(w, sig_field_spec=fields.SigFieldSpec(
                'SaoSignature2',
                box=(x, y, x2, y2)
            ))
            meta = signers.PdfSignatureMetadata(field_name='SaoSignature2')
            pdf_signer = signers.PdfSigner(meta, signer=signer, stamp_style=stamp.TextStampStyle(
                stamp_text='\n\n\nSigned by: %(signer)s\nDate Signed: %(ts)s',
                background=pdf_image,
                border_width=0
            ))

            with open(output_path, 'wb') as outf:
                pdf_signer.sign_pdf(w, output=outf)

        os.remove(cert_path)
        os.remove(key_path)

    def leave_application_sign_pdf_sync_cao(self, input_path: str, output_path: str, image_path: str, p12_data: bytes, p12_password: str) -> None:
        cert_path, key_path = PDFSigner.extract_cert_and_key(p12_data, p12_password)
        signer = signers.SimpleSigner.load(key_path, cert_path)
        pdf_image = PdfImage(image_path)

        x = 200  # move x axis | left: decrease | right: increase
        y = 155  # increase the value to move up
        x2 = x + 220
        y2 = y + 70


        with open(input_path, 'rb') as inf:
            w = IncrementalPdfFileWriter(inf)
            fields.append_signature_field(w, sig_field_spec=fields.SigFieldSpec(
                'CaoSignature2',
                box=(x, y, x2, y2)
            ))
            meta = signers.PdfSignatureMetadata(field_name='CaoSignature2')
            pdf_signer = signers.PdfSigner(meta, signer=signer, stamp_style=stamp.TextStampStyle(
                stamp_text='\n\n\nSigned by: %(signer)s\nDate Signed: %(ts)s',
                background=pdf_image,
                border_width=0
            ))

            with open(output_path, 'wb') as outf:
                pdf_signer.sign_pdf(w, output=outf)

        os.remove(cert_path)
        os.remove(key_path)    