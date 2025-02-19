from PIL import Image, ImageEnhance

class ImageProcessor:
    @staticmethod
    def process_signature_image(input_path: str, output_path: str, scale_factor: float = 0.9, quality: int = 95):
        """
        Process signature image by resizing and enhancing quality
        :param input_path: Path to input image
        :param output_path: Path to save processed image
        :param scale_factor: Factor to scale image (0.9 = 90% of original size)
        :param quality: Output image quality (1-100)
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
            img = enhancer.enhance(1.2)  # Increase contrast by 20%
            
            # Save with high quality
            img.save(output_path, 'PNG', quality=quality, optimize=True)
