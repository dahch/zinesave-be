import io
import textwrap
from datetime import datetime, timezone
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont

# Directory Configuration
# COVERS_DIR = "outputs/covers"
# os.makedirs(COVERS_DIR, exist_ok=True)

# Layout Settings (Modern Editorial Style)
WIDTH = 1600
HEIGHT = 2560
PADDING = 120  # Side margin
BACKGROUND_COLOR = "#1a1a1a"  # Very dark grey (better than pure black for screens)
TEXT_COLOR = "#FFFFFF"
ACCENT_COLOR = "#3B82F6" 
BORDER_WIDTH = 40

def get_font(name_choices, size):
    """
    Try loading common fonts. If not, use the default but warn.
    To make it look GOOD, download 'Roboto-Bold.ttf' or 'Montserrat-Bold.ttf' 
    and put them in the same folder.
    """
    # List of sources to test in order of priority
    font_paths = [
        "Roboto-Bold.ttf",      # Ideal: Download it from Google Fonts
        "Arial Bold.ttf",
        "arialbd.ttf",          # Common Windows
        "/Library/Fonts/Arial Bold.ttf", # Standard Mac
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", # Docker/Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", # Common Linux
        "arial.ttf"
    ]
    
    # We add the ones you passed as an argument.
    if isinstance(name_choices, list):
        font_paths = name_choices + font_paths
    elif isinstance(name_choices, str):
        font_paths.insert(0, name_choices)

    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
            
    print("⚠️ Warning: No nice TTF font found. Using default.")
    return ImageFont.load_default()

def draw_text_centered(draw, text, font, color, center_x, start_y, max_width, line_spacing=1.2):
    """Draw centred text with automatic line adjustment."""
    lines = textwrap.wrap(text, width=int(max_width / (font.getbbox("A")[2] * 0.9))) # Character estimation
    
    # If textwrap fails or the font is variable, we make a more precise manual adjustment.
    # (Optional: here I use simple textwrap logic so as not to overcomplicate the code).
    
    current_y = start_y
    for line in lines:
        # Calculate line width to centre it
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        
        x = center_x - (text_w / 2)
        draw.text((x, current_y), line, font=font, fill=color)
        current_y += text_h * line_spacing
        
    return current_y # Return to the final Y to continue drawing below

def generate_cover(title: str, url: str, job_id: str):
    img = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(img)

    #1. Load Fonts (MUCH larger sizes)
    # Large title for impact
    title_font = get_font([
        "Roboto-Bold.ttf", 
        "arialbd.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    ], 180) 
    # Subtitle (domain)
    subtitle_font = get_font([
        "Roboto-Regular.ttf", 
        "arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    ], 60)
    # Small footer
    footer_font = get_font([
        "Roboto-Light.ttf", 
        "arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf" # Fallback to Italic or Regular as Light might not be present
    ], 40)

    domain = urlparse(url).netloc.upper() # Domain names in capital letters look better.
    date = datetime.now(timezone.utc).strftime("%B %d, %Y").upper()

    # 2. Draw Frame/Border (Visual Style)
    draw.rectangle(
        [(PADDING/2, PADDING/2), (WIDTH - PADDING/2, HEIGHT - PADDING/2)],
        outline=ACCENT_COLOR,
        width=10
    )

    # 3. Draw "Header" (Domain and Date at the top or Category)
    # Let's put the Domain at the top, centred.
    draw_text_centered(
        draw, 
        domain, 
        subtitle_font, 
        ACCENT_COLOR, 
        WIDTH / 2, 
        PADDING + 100, 
        WIDTH - (PADDING * 2)
    )

    # 4. Draw Title (In the visual centre)
    # We calculate an approximate Y start point. 
    # To make it perfectly vertically centred, we would need to measure the entire block beforehand,
    # but starting at 35% of the height usually works well for covers.
    title_y_start = HEIGHT * 0.30
    
    last_y = draw_text_centered(
        draw,
        title,
        title_font,
        TEXT_COLOR,
        WIDTH / 2,
        title_y_start,
        WIDTH - (PADDING * 2.5) # Internal margin for text
    )

    #5. Decorative line below the title
    line_width = 200
    line_y = last_y + 80
    draw.rectangle(
        [( (WIDTH/2) - (line_width/2), line_y), ((WIDTH/2) + (line_width/2), line_y + 10)],
        fill=ACCENT_COLOR
    )

    # 6. Footer (Date at the bottom)
    draw.text(
        (WIDTH / 2, HEIGHT - PADDING - 100),
        f"GENERATED • {date}",
        fill="#888888", # Soft grey for secondary information
        font=footer_font,
        anchor="ms" # Middle-South anchor (centrado horizontal, base vertical)
    )

    # path = os.path.join(COVERS_DIR, f"{job_id}_cover.jpg")
    # img.save(path, "JPEG", quality=95)
    
    # return path
    output = io.BytesIO()
    img.save(output, format="JPEG", quality=95)
    output.seek(0)
    return output