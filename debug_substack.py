import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.google.com/",
}

url = "https://blog.bytebytego.com/p/a-crash-course-in-redis"
response = requests.get(url, headers=HEADERS)
print(f"Status: {response.status_code}")

soup = BeautifulSoup(response.text, "html.parser")
images = soup.find_all("img")
print(f"Found {len(images)} images.")

for i, img in enumerate(images[:5]):  # Print first 5
    print(f"Image {i}: {img.attrs}")

# Check specifically for the diagram
text_node = soup.find(string=lambda t: "Below is a high-level diagram" in str(t))
if text_node:
    print("\n--- Context around diagram ---")
    parent = text_node.parent
    # Print next few siblings
    curr = parent.next_sibling
    for _ in range(3):
        if curr:
            print(f"Sibling: {curr}")
            curr = curr.next_sibling
