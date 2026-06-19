from PIL import Image, ImageDraw, ImageFont
import logging
import json

ORANGE = (255, 103, 0)  # #FF6700
FONT_PATH = "public/assets/HelveticaNeueBold.otf"
FONT_SIZE = 60
LETTER_SPACING = 5




def load_font(path: str, size: int = 60) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except IOError:
        logging.error(f"Font file not found: {path}")
        raise RuntimeError(f"Font file not found: {path}")


def text_width(draw: ImageDraw, text: str, font) -> int:
    total = 0
    for ch in text:
        bb = draw.textbbox((0, 0), ch, font=font)
        total += bb[2] - bb[0]
    return total + LETTER_SPACING * (len(text) - 1)


def draw_centered(draw: ImageDraw, text: str, font, cx: float, cy: float, fill: tuple) -> None:
    total_w = text_width(draw, text, font)
    ref_bb = draw.textbbox((0, 0), text, font=font)
    h = ref_bb[3] - ref_bb[1]

    x = cx - total_w / 2
    y = cy - h / 2 - ref_bb[1]

    for ch in text:
        bb = draw.textbbox((0, 0), ch, font=font)
        draw.text((x - bb[0], y), ch, font=font, fill=fill)
        x += (bb[2] - bb[0]) + LETTER_SPACING


def generate_og_image(
    report_path: str,
    template_path: str = "public/assets/meta_tags_template.png",
    output_path: str = "public/assets/meta_tags_image.png",
) -> None:
    with open(report_path) as f:
        data = json.load(f)

    total_tracks = data["total_tracks"]
    total_streams_b = round(data["total_streams"] / 1_000_000_000)
    total_artists = data["total_artists"]

    img = Image.open(template_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    f_number = load_font(FONT_PATH)

    # padding=50, card1=349, gap1=26, card2=349, gap2=27, card3=349
    CARD_W = 349
    CARD_CENTERS_X = [
        50 + CARD_W // 2,
        50 + CARD_W + 26 + CARD_W // 2,
        50 + CARD_W + 26 + CARD_W + 27 + CARD_W // 2,
    ]

    value_cy = 490

    stats = [
        f"{total_tracks:,}".replace(",", " "),
        f"{total_streams_b:,}B".replace(",", " "),
        f"{total_artists:,}".replace(",", " "),
    ]

    for cx, number in zip(CARD_CENTERS_X, stats):
        draw_centered(draw, number, f_number, cx, value_cy, ORANGE)

    img.save(output_path, "PNG", optimize=True)