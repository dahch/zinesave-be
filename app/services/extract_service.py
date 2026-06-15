import json
import logging

import requests
from bs4 import BeautifulSoup
from readability import Document
from sqlalchemy.orm import Session

from app.domain.models.job import Job
from app.domain.models.job_content import JobContent
from app.services.metadata_service import extract_metadata

logger = logging.getLogger(__name__)
    
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.google.com/",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

def extract_content(db: Session, job: Job):
    #1 Download HTML
    logger.info(f"Downloading HTML from {job.source_url}")
    response = requests.get(job.source_url, headers=HEADERS, timeout=10)
    response.raise_for_status()



    html = response.text
    
    # 1.5 Preprocess HTML to rescue images (Substack/Medium)
    soup = BeautifulSoup(html, "lxml")
    
    # Substack: div.captioned-image-container > figure
    for container in soup.find_all("div", class_="captioned-image-container"):
        img = container.find("img")
        if img:
            # Clean attributes that might confuse readers
            if "srcset" in img.attrs: del img["srcset"]
            if "sizes" in img.attrs: del img["sizes"]
            if "loading" in img.attrs: del img["loading"]
            
            # Replace complex container with simple p > img
            p = soup.new_tag("p")
            p.append(img)
            container.replace_with(p)
            
    # Generic Figure unwrapping (often stripped by readability)
    for figure in soup.find_all("figure"):
        img = figure.find("img")
        if img:
            if "srcset" in img.attrs: del img["srcset"]
            p = soup.new_tag("p")
            p.append(img)
            figure.replace_with(p)

    html = str(soup)

    #2 Extract Metadata (from RAW HTML)    
    metadata = extract_metadata(html, job.source_url)
    
    # Save Metadata as JobContent
    meta_content = JobContent(
        job_id=job.id,
        step="metadata",
        content_type="json",
        content=json.dumps(metadata)
    )
    db.add(meta_content)

    #3 Reader mode
    doc = Document(html)
    cleaned_html = doc.summary(html_partial=True)
    title = doc.short_title()
    logger.info(f"Extracted content for {title}")

    #3 Save extracted content
    content = JobContent(
        job_id=job.id,
        step="extracted",
        content_type="html",
        content=cleaned_html
    )

    db.add(content)

    #4 Update Job
    job.current_step = "extracting"
    job.progress = 25

    db.commit()

    return {
        "title": title,
        "html": cleaned_html,
        "metadata": metadata
    }