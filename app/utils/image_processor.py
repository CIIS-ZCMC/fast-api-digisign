"""
Image Processing Utility

This module provides functionality for processing signature images before they are
applied to PDF documents. It handles image format conversion, resizing, and quality
enhancement to ensure optimal appearance of signatures in the final document.

The module uses the PIL (Python Imaging Library) for all image processing operations.
"""

from PIL import Image, ImageEnhance

class ImageProcessor:
    """
    A utility class for processing signature images.
    
    This class provides methods to enhance and optimize signature images for use
    in PDF documents. It handles format conversion, resizing, and quality improvements
    through various image processing techniques.
    """

    @staticmethod
    def process_signature_image(input_path: str, output_path: str, scale_factor: float = 0.9, quality: int = 95) -> None:
        """
        Process a signature image by applying various enhancements and optimizations.
        
        This method performs the following operations:
        1. Converts the image to RGBA format if needed
        2. Resizes the image according to the scale factor
        3. Enhances image sharpness by 50%
        4. Increases image contrast by 40%
        5. Saves the processed image with specified quality

        Args:
            input_path (str): Path to the input signature image
            output_path (str): Path where the processed image will be saved
            scale_factor (float, optional): Factor to scale image. Defaults to 0.9 (90% of original size)
            quality (int, optional): Output image quality (1-100). Defaults to 95

        Note:
            - The image is always saved in PNG format for optimal transparency support
            - LANCZOS resampling is used for high-quality resizing
            - The output is optimized for file size while maintaining quality
        """
        with Image.open(input_path) as img:
            # Convert to RGBA if not already
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            # Get original size
            original_width, original_height = img.size
            
            # Calculate new size (reduce by scale_factor)
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            
            # Resize image using high-quality resampling
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Enhance image
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.5)  # Increase sharpness by 50%
            
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.4)  # Increase contrast by 40%
            
            # Save with high quality
            img.save(output_path, 'PNG', quality=quality, optimize=True)
