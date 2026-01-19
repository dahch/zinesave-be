from urllib.parse import urljoin, urlparse

def resolve_url(src: str, base_url: str) -> str | None:
    if not src:
        return None

    src = src.strip()

    # Data URI -> return same
    if src.startswith("data:image"):
        return src

    parsed = urlparse(src)

    # Absolute (http / https)
    if parsed.scheme in ("http", "https"):
        return src

    # Relative protocol (//cdn.site.com/img.png)
    if src.startswith("//"):
        base_scheme = urlparse(base_url).scheme or "https"
        return f"{base_scheme}:{src}"

    # Relative -> resolve
    return urljoin(base_url, src)