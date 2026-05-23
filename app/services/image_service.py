import uuid
import logging
import requests
from PIL import Image
import io
from bs4 import BeautifulSoup
from app.services.url_utils import resolve_url
from ebooklib import epub

logger = logging.getLogger(__name__)

def process_images(html: str, base_url: str):
    soup = BeautifulSoup(html, "html.parser")
    image_items = []

    for img in soup.find_all("img"):
        src = img.get("src")
        resolved = resolve_url(src, base_url)
        logger.debug(f"Processing image: {resolved}")
        
        #Data URI
        if resolved and resolved.startswith("data:image"):
            continue

        if not resolved:
            img.decompose()
            continue

        try:
            response = requests.get(resolved, timeout=10)
            response.raise_for_status()

            # Optimize Image with Pillow

            image_data = response.content
            
            try:
                with Image.open(io.BytesIO(image_data)) as pil_img:
                    # 1. Convert to RGB if necessary (except PNG with alpha)
                    if pil_img.mode in ("RGBA", "LA") or (pil_img.mode == "P" and "transparency" in pil_img.info):
                        # Keep PNG for transparency
                        final_format = "PNG"
                        mime_type = "image/png"
                        ext = "png"
                    else:
                        pil_img = pil_img.convert("RGB")
                        final_format = "JPEG"
                        mime_type = "image/jpeg"
                        ext = "jpg"

                    # 2. Resize if too large
                    max_width = 1200
                    if pil_img.width > max_width:
                        ratio = max_width / pil_img.width
                        new_height = int(pil_img.height * ratio)
                        pil_img = pil_img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                    
                    # 3. Export to Bytes
                    output_buffer = io.BytesIO()
                    if final_format == "JPEG":
                        pil_img.save(output_buffer, format="JPEG", quality=85, optimize=True)
                    else:
                        pil_img.save(output_buffer, format="PNG", optimize=True)
                    
                    optimized_content = output_buffer.getvalue()

            except Exception as img_err:
                logger.warning(f"Image optimization failed for {resolved}, using original: {img_err}")
                optimized_content = image_data
                content_type = response.headers.get("Content-Type", "")
                ext = content_type.split("/")[-1].split(";")[0] or "png"
                mime_type = content_type

            filename = f"{uuid.uuid4()}.{ext}"

            epub_image = epub.EpubImage()
            epub_image.file_name = f"images/{filename}"
            epub_image.media_type = mime_type
            epub_image.content = optimized_content


            image_items.append(epub_image)

            #Overwrite src with epub path
            img["src"] = epub_image.file_name

        except Exception as e:
            logger.warning(f"Error handling image {resolved}: {str(e)}")
            # Fail silently: quality > crash
            img.decompose()
    
    return str(soup), image_items