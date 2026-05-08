from __future__ import annotations

import math
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ICLOUD = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/Glasgow Branch RCOP/Scottish Conference 2026"
ASSETS = ICLOUD / "Assets"
OUT_DIR = ASSETS / "Speaker Videos"
CAPTION_DIR = ASSETS / "Speaker Captions"
AUDIO = ROOT / "assets/audio/scottish-conference-underscore.wav"

W, H = 1080, 1920
FPS = 30
DURATION = 12
FRAMES = FPS * DURATION

GREEN = "#007F63"
DEEP = "#051B2C"
NAVY = "#07356E"
PALE = "#D9E9F5"
WHITE = "#FFFFFF"
RED = "#C8193C"


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("/System/Library/Fonts/Supplemental") / name,
        Path("/Library/Fonts") / name,
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


FONT_BLACK = font("Arial Bold.ttf", 76)
FONT_HEAVY = font("Arial Bold.ttf", 58)
FONT_BOLD = font("Arial Bold.ttf", 42)
FONT_MED = font("Arial.ttf", 35)
FONT_SMALL = font("Arial Bold.ttf", 28)
FONT_TINY = font("Arial.ttf", 24)


SPEAKERS = [
    {
        "slug": "01-dr-george-moncrieff",
        "name": "Dr George Moncrieff",
        "asset": "Dr George Moncrieff speaker graphic.png",
        "hook": "Dermatology focus",
        "talk": "Dermatology below the Wallace Line",
        "time": "09:15 Plenary 1",
        "detail": "Plus afternoon Dermoscopy session",
        "caption": "Dermatology and dermoscopy are key parts of everyday podiatry practice. Join Dr George Moncrieff at Scottish Conference 2026 for Dermatology below the Wallace Line, plus an afternoon dermoscopy session.",
    },
    {
        "slug": "02-maria-dow",
        "name": "Maria Dow",
        "asset": "Maria Dow speaker graphic.png",
        "hook": "Weight management",
        "talk": "The Changing Landscape of Weight Management",
        "time": "11:30 Plenary 2",
        "detail": "Including Weight Loss Jabs: A Paradigm Shift?",
        "caption": "Weight loss medications are changing clinical conversations across healthcare. Maria Dow will explore what this means for patient care and the wider healthcare landscape at Scottish Conference 2026.",
    },
    {
        "slug": "03-dr-charlotte-holley",
        "name": "Dr Charlotte Holley",
        "asset": "Dr Charlotte Holley speaker graphic.png",
        "hook": "Children's podiatry",
        "talk": "Children's Podiatry",
        "time": "13:30 Concurrent Session B",
        "detail": "Prevention. Early intervention. Long-term impact.",
        "caption": "Dr Charlotte Holley joins Scottish Conference 2026 for a focused session on children's podiatry, prevention and early intervention. A valuable session for anyone interested in paediatrics and long-term foot health.",
    },
    {
        "slug": "04-graham-pirie",
        "name": "Graham Pirie",
        "asset": "Graham Pirie speaker graphic.png",
        "hook": "Scottish update",
        "talk": "500 Miles and More",
        "time": "Afternoon programme",
        "detail": "A Scottish update for the profession",
        "caption": "Join Graham Pirie for 500 Miles and More, a Scottish update in the afternoon programme at Scottish Conference 2026.",
    },
    {
        "slug": "05-emma-noe",
        "name": "Emma Noe",
        "asset": "Emma Noe speaker graphic.png",
        "hook": "Conference welcome",
        "talk": "Welcome and Question Time",
        "time": "09:05 Welcome | Afternoon panel",
        "detail": "Helping open the day and close the discussion",
        "caption": "Emma Noe helps welcome delegates to Scottish Conference 2026 and joins the afternoon Question Time discussion.",
    },
    {
        "slug": "06-jane-pritchard",
        "name": "Jane Pritchard",
        "asset": "Jane Pritchard speaker graphic.png",
        "hook": "Question Time",
        "talk": "Question Time Panel",
        "time": "Afternoon programme",
        "detail": "Discussion, professional insight and audience questions",
        "caption": "Jane Pritchard joins the Question Time panel at Scottish Conference 2026, bringing professional insight and discussion to the afternoon programme.",
    },
]


def ease(x: float) -> float:
    x = max(0, min(1, x))
    return 1 - (1 - x) ** 3


def alpha_in(t: float, start: float, dur: float = 0.45) -> int:
    return int(255 * ease((t - start) / dur))


def rounded(im: Image.Image, radius: int) -> Image.Image:
    mask = Image.new("L", im.size, 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle((0, 0, im.width, im.height), radius=radius, fill=255)
    out = Image.new("RGBA", im.size)
    out.paste(im, (0, 0), mask)
    return out


def draw_wrapped(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fnt, fill, width: int, line_gap: int = 8) -> int:
    x, y = xy
    lines: list[str] = []
    for para in text.split("\n"):
        words = para.split()
        cur = ""
        for word in words:
            test = f"{cur} {word}".strip()
            if draw.textbbox((0, 0), test, font=fnt)[2] <= width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + line_gap
    return y


def paste_text_layer(base: Image.Image, make_layer, opacity: int) -> None:
    if opacity <= 0:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    make_layer(ImageDraw.Draw(layer))
    if opacity < 255:
        layer.putalpha(layer.getchannel("A").point(lambda a: a * opacity // 255))
    base.alpha_composite(layer)


def make_bg(t: float) -> Image.Image:
    img = Image.new("RGBA", (W, H), GREEN)
    draw = ImageDraw.Draw(img)
    for y in range(0, H, 54):
        c = (255, 255, 255, 13 if y % 108 == 0 else 7)
        draw.line((0, y + int(10 * math.sin(t * 0.7 + y)), W, y + int(10 * math.sin(t * 0.7 + y))), fill=c, width=2)
    draw.ellipse((-320, -260, 520, 540), fill=(0, 47, 84, 135))
    draw.ellipse((650, 980, 1420, 1780), fill=(0, 47, 84, 90))
    return img


def render_speaker(s: dict[str, str]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CAPTION_DIR.mkdir(parents=True, exist_ok=True)
    src = ASSETS / s["asset"]
    speaker = Image.open(src).convert("RGBA")
    speaker = ImageEnhance.Sharpness(speaker).enhance(1.08)

    out = OUT_DIR / f"{s['slug']}-speaker-reel.mp4"
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgba",
        "-s",
        f"{W}x{H}",
        "-r",
        str(FPS),
        "-i",
        "-",
        "-stream_loop",
        "-1",
        "-i",
        str(AUDIO),
        "-t",
        str(DURATION),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "150k",
        "-shortest",
        str(out),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None

    for frame in range(FRAMES):
        t = frame / FPS
        im = make_bg(t)
        draw = ImageDraw.Draw(im)

        # Speaker graphic card, gently zooming in.
        card_w = 960
        scale = card_w / speaker.width * (1.0 + 0.035 * t / DURATION)
        card_h = int(speaker.height * scale)
        resized = speaker.resize((int(speaker.width * scale), card_h), Image.Resampling.LANCZOS)
        card = rounded(resized, 46)
        x = (W - card.width) // 2
        y = 118 - int(18 * ease(t / DURATION))
        shadow = Image.new("RGBA", card.size, (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rounded_rectangle((0, 0, card.width, card.height), 46, fill=(0, 0, 0, 120))
        shadow = shadow.filter(ImageFilter.GaussianBlur(24))
        im.alpha_composite(shadow, (x, y + 18))
        im.alpha_composite(card, (x, y))

        # Lower content panel.
        panel_y = 980
        draw.rounded_rectangle((58, panel_y, 1022, 1684), radius=44, fill=(217, 233, 245, 245))
        draw.rounded_rectangle((58, panel_y, 1022, 1684), radius=44, outline=(255, 255, 255, 210), width=3)
        draw.rectangle((58, 1716, 1022, 1740), fill=RED)
        draw.rectangle((58, 1744, 1022, 1764), fill=WHITE)
        draw.rectangle((58, 1768, 1022, 1792), fill=NAVY)

        # Animated text sections.
        paste_text_layer(
            im,
            lambda d: (
                d.rounded_rectangle((98, 1018, 454, 1076), radius=20, fill=NAVY),
                d.text((124, 1030), "SPEAKER SPOTLIGHT", font=FONT_SMALL, fill=WHITE),
                d.text((98, 1102), s["name"], font=FONT_BLACK, fill=(17, 20, 38)),
            ),
            alpha_in(t, 0.25),
        )

        paste_text_layer(
            im,
            lambda d: (
                d.text((98, 1225), s["hook"].upper(), font=FONT_SMALL, fill=(0, 127, 99)),
                draw_wrapped(d, (98, 1272), s["talk"], FONT_HEAVY, (17, 20, 38), 850, 10),
            ),
            alpha_in(t, 2.3),
        )

        paste_text_layer(
            im,
            lambda d: (
                d.rounded_rectangle((98, 1488, 982, 1608), radius=26, fill=(255, 255, 255, 245)),
                d.text((130, 1514), s["time"], font=FONT_BOLD, fill=(7, 53, 110)),
                d.text((130, 1562), s["detail"], font=FONT_TINY, fill=(38, 58, 76)),
            ),
            alpha_in(t, 4.5),
        )

        paste_text_layer(
            im,
            lambda d: (
                d.rounded_rectangle((104, 1818, 976, 1894), radius=28, fill=(7, 27, 44, 238)),
                d.text((148, 1839), "Book: glasgowrcop.org/SC26", font=FONT_BOLD, fill=WHITE),
            ),
            alpha_in(t, 7.4),
        )

        proc.stdin.write(im.tobytes())

    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError(f"ffmpeg failed for {s['name']}")

    caption = (
        f"{s['name']} at The Scottish Conference 2026.\n\n"
        f"{s['caption']}\n\n"
        "Join the Royal College of Podiatry Scottish Branches Network on Saturday 23 May 2026 "
        "at Stirling Court Hotel, University of Stirling.\n\n"
        "Book your place: https://glasgowrcop.org/SC26\n"
    )
    (CAPTION_DIR / f"{s['slug']}-caption.txt").write_text(caption, encoding="utf-8")


def main() -> None:
    for speaker in SPEAKERS:
        print(f"Rendering {speaker['name']}...")
        render_speaker(speaker)


if __name__ == "__main__":
    main()
