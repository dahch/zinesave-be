from bs4 import BeautifulSoup
from langdetect import detect
from sqlalchemy.orm import Session

from app.domain.models.job import Job
from app.domain.models.job_content import JobContent

BASE_CSS = """
body {
    font-family: serif;
    line-height: 1.6;
}
h1, h2, h3 {
    margin-top: 1.2em;
}
img {
    max-width: 100%;
}
"""


def process_html_normalization(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")

    # 2 Remove trash
    for tag in soup(["script", "style", "iframe", "noscript"]):
        tag.decompose()

    # 3 Normalize headings (only one h1)
    h1s = soup.find_all("h1")
    if len(h1s) > 1:
        for h in h1s[1:]:
            h.name = "h2"

    # 4 Clean up dangerous tags
    for tag in soup.find_all(True):
        tag.attrs = {k: v for k, v in tag.attrs.items() if k in ["href", "src", "alt"]}

    # 5 Detect language and word count
    text = soup.get_text(separator=" ")
    language = "unknown"
    try:
        language = detect(text)
    except Exception:
        pass

    word_count = len(text.split())

    # 6 Inject CSS
    head = soup.find("head")
    if not head:
        head = soup.new_tag("head")
        soup.insert(0, head)

    style = soup.new_tag("style")
    style.string = BASE_CSS
    head.append(style)

    return {"html": str(soup), "language": language, "word_count": word_count}


def normalize_html(db: Session, job: Job):
    # 1 Get extracted html
    extracted = (
        db.query(JobContent)
        .filter(
            JobContent.job_id == job.id,
            JobContent.step == "extracted",
            JobContent.content_type == "html",
        )
        .first()
    )

    if not extracted:
        raise Exception("Extracted content not found")

    result = process_html_normalization(extracted.content)

    # 7 Save normalized content
    content = JobContent(
        job_id=job.id, step="normalized", content_type="html", content=result["html"]
    )

    db.add(content)

    # 8 Update Job
    job.current_step = "normalizing"
    job.progress = 50

    db.commit()

    return {"language": result["language"], "word_count": result["word_count"]}
