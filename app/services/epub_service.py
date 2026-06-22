import json
import logging
import os
import tempfile

from ebooklib import epub
from sqlalchemy.orm import Session

from app.domain.models.file import File
from app.domain.models.job import Job
from app.domain.models.job_content import JobContent
from app.services.cover_service import generate_cover
from app.services.image_service import process_images
from app.services.metadata_service import extract_metadata
from app.services.storage_service import storage_service

logger = logging.getLogger(__name__)

# OUTPUT_DIR = "outputs"
# os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_epub(db: Session, job: Job):
    logger.info(f"Generating EPUB for job {job.id}")

    is_composite = job.base_url == "composite"

    # 1 Get normalized html(s)
    if is_composite:
        contents = (
            db.query(JobContent)
            .filter(
                JobContent.job_id == job.id,
                JobContent.step.like("normalized_%"),
                JobContent.content_type == "html",
            )
            .all()
        )
        if not contents:
            raise ValueError("No normalized html found for composite job")

        normalized_contents = sorted(contents, key=lambda c: int(c.step.split("_")[1]))

        meta_content = (
            db.query(JobContent)
            .filter(JobContent.job_id == job.id, JobContent.step == "composite_meta")
            .first()
        )
        urls = json.loads(meta_content.content).get("urls", []) if meta_content else []
    else:
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

        normalized_contents = [normalized]
        urls = [job.source_url]

    # 2. Get Metadata (Stored JSON)
    meta_record = (
        db.query(JobContent)
        .filter(
            JobContent.job_id == job.id,
            JobContent.step == "metadata",
            JobContent.content_type == "json",
        )
        .first()
    )

    if meta_record:
        metadata = json.loads(meta_record.content)
    else:
        # Fallback if old job or missing
        html_with_images, _ = process_images(normalized_contents[0].content, urls[0])
        metadata = extract_metadata(html_with_images, urls[0])

    # 3 Create epub
    book = epub.EpubBook()

    book.set_title(metadata["title"])
    book.set_language(metadata.get("language", "en"))
    book.add_author(metadata.get("author", "Unknown"))
    book.add_metadata("DC", "publisher", metadata.get("publisher", ""))
    book.add_metadata("DC", "date", metadata.get("published", ""))
    book.add_metadata("DC", "source", metadata.get("source", ""))

    book.set_identifier(job.id)

    # Returns BytesIO now
    cover_bytes = generate_cover(title=metadata["title"], url=job.base_url, job_id=job.id)

    book.set_cover("cover.jpg", cover_bytes.getvalue())

    chapters = []
    all_images = []

    from bs4 import BeautifulSoup

    for i, norm in enumerate(normalized_contents):
        url = urls[i] if i < len(urls) else job.source_url
        html_with_images, images = process_images(norm.content, url)

        soup = BeautifulSoup(html_with_images, "lxml")
        h1 = soup.find("h1")
        ch_title = h1.text if h1 else f"Chapter {i+1}"

        chapter = epub.EpubHtml(
            title=ch_title,
            file_name=f"chapter_{i+1}.xhtml",
            lang=metadata.get("language", "en"),
        )
        chapter.content = html_with_images
        chapters.append(chapter)
        all_images.extend(images)

    # 4 Add chapters and images to book
    for chapter in chapters:
        book.add_item(chapter)

    for img in all_images:
        book.add_item(img)

    # 5 TOC + Spine
    book.toc = tuple(
        epub.Link(f"chapter_{i+1}.xhtml", ch.title, f"chapter_{i+1}")
        for i, ch in enumerate(chapters)
    )
    book.spine = ["nav"] + chapters

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
        path=key,  # Storing S3 Key
        size_bytes=size,
    )
    db.add(file_record)

    # 9 Update job
    job.current_step = "generating"
    job.progress = 75

    db.commit()

    logger.info(f"EPUB generated and uploaded to {key}")
    return key
