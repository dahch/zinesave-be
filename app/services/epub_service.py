import os
import json
from ebooklib import epub
from sqlalchemy.orm import Session

from app.domain.models.job import Job
from app.domain.models.job_content import JobContent
from app.domain.models.file import File

from app.services.image_service import process_images
from app.services.cover_service import generate_cover
from app.services.metadata_service import extract_metadata


import logging
import tempfile
from app.services.storage_service import storage_service

logger = logging.getLogger(__name__)

# OUTPUT_DIR = "outputs"
# os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_epub(db: Session, job: Job):
    logger.info(f"Generating EPUB for job {job.id}")
    # 1 Get normalized html
    normalized = (
        db.query(JobContent)
        .filter(
            JobContent.job_id == job.id,
            JobContent.step == "normalized",
            JobContent.content_type == "html",
        )
        .first()
    )

    if not normalized:
        raise ValueError("No normalized html found for job")
    
    # 2. Get Metadata (Stored JSON)
    meta_record = (
        db.query(JobContent)
        .filter(
            JobContent.job_id == job.id,
            JobContent.step == "metadata",
            JobContent.content_type == "json"
        )
        .first()
    )
    
    if meta_record:
        metadata = json.loads(meta_record.content)
    else:
        # Fallback if old job or missing
        html_with_images, _ = process_images(normalized.content, job.source_url)
        metadata = extract_metadata(html_with_images, job.source_url)

    # 3 Create epub
    book = epub.EpubBook()

    html_with_images, images = process_images(normalized.content, job.source_url)
    # metadata = extract_metadata(html_with_images, job.source_url) <-- REMOVED

    book.set_title(metadata["title"])
    book.set_language(metadata["language"])
    book.add_author(metadata["author"])
    book.add_metadata("DC", "publisher", metadata["publisher"])
    book.add_metadata("DC", "date", metadata["published"])
    book.add_metadata("DC", "source", metadata["source"])

    book.set_identifier(job.id)

    # Returns BytesIO now
    cover_bytes = generate_cover(
        title=metadata["title"],
        url=job.base_url,
        job_id=job.id
    )

    book.set_cover("cover.jpg", cover_bytes.getvalue())

    # 3 Add chapter
    chapter = epub.EpubHtml(
        title=metadata["title"],
        file_name="chapter_1.xhtml",
        lang=metadata["language"],
    )
    chapter.content = html_with_images

    # 4 Add chapter to book
    book.add_item(chapter)

    for img in images:
        book.add_item(img)

    # 5 TOC + Spine
    book.toc = (
        epub.Link("chapter_1.xhtml", metadata["title"], "chapter"),
    )
    book.spine = ["nav", chapter]

    # 6 Required files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # 7 Write to temp file & Upload
    with tempfile.NamedTemporaryFile(suffix=".epub", delete=True) as tmp:
        epub.write_epub(tmp.name, book)
        
        # Rewind to read bytes for upload check if needed, but write_epub closes file?
        # write_epub takes path.
        
        key = f"epubs/{job.id}.epub"
        size = os.path.getsize(tmp.name)
        
        with open(tmp.name, "rb") as f:
            storage_service.upload_file(f, key)

    # 8 Register file (store Key in path)
    file_record = File(
        job_id=job.id,
        type="epub",
        path=key, # Storing S3 Key
        size_bytes=size,
    )
    db.add(file_record)

    # 9 Update job
    job.current_step = "generating"
    job.progress = 75

    db.commit()

    logger.info(f"EPUB generated and uploaded to {key}")
    return key
