#!/usr/bin/env python3
"""Generate the canonical KC x LT signature assets and banner embeddings.

The public mark is intentionally built from explicit cubic Bezier strokes rather
than a font.  This keeps the four initials recognisable, the animation order
predictable, and every exported asset independent of installed typefaces.
"""

from __future__ import annotations

import argparse
import math
import re
import struct
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BRAND_DIR = ROOT / "assets" / "brand"
BANNER_FILES = (
    ROOT / "assets" / "profile-banner-animated.svg",
    ROOT / "assets" / "profile-banner-static.svg",
    ROOT / "assets" / "profile-banner-mobile-animated.svg",
    ROOT / "assets" / "profile-banner-mobile-static.svg",
)

INK_STOPS = ((0.0, "#155eef"), (0.52, "#0a6fc2"), (1.0, "#0b82e8"))
INK_RGB = ((21, 94, 239), (10, 111, 194), (11, 130, 232))


@dataclass(frozen=True)
class Stroke:
    name: str
    path: str
    duration: str
    delay: str


# Canonical full-size geometry.  KC and LT are two visually distinct pairs:
# the open C ends before the simple L begins, creating an intentional pen lift.
PRIMARY_STROKES = (
    Stroke("K stem", "M122 40C112 99 101 161 92 208", ".32s", "0s"),
    Stroke("K upper arm", "M110 116C141 94 169 67 199 39", ".26s", ".24s"),
    Stroke("K lower arm", "M111 119C139 145 166 171 198 190", ".28s", ".42s"),
    Stroke("C", "M323 76C300 45 255 46 231 79C205 115 210 165 240 185C269 204 307 187 326 155", ".52s", ".62s"),
    Stroke("L", "M397 42C386 98 375 151 365 187C391 190 420 183 447 169", ".34s", "1.24s"),
    Stroke("T stem", "M560 59C548 102 536 149 526 191", ".32s", "1.55s"),
    Stroke("T bar", "M477 70C530 52 592 52 649 66", ".28s", "1.82s"),
    Stroke("underline", "M66 232C185 214 314 216 430 223C520 229 602 225 666 207", ".55s", "2.05s"),
)


# Purpose-built small geometry.  It preserves the same letter construction but
# uses wider spacing and fewer inflections so it survives banner/share scaling.
COMPACT_STROKES = (
    Stroke("K stem", "M63 28C57 63 51 104 45 153", ".32s", "0s"),
    Stroke("K upper arm", "M55 84C76 68 90 51 106 34", ".26s", ".24s"),
    Stroke("K lower arm", "M55 87C74 104 91 121 108 133", ".28s", ".42s"),
    Stroke("C", "M165 62C153 45 129 46 116 65C103 86 105 115 121 129C137 141 156 131 166 112", ".52s", ".62s"),
    Stroke("L", "M209 36C203 70 196 106 190 136C206 138 223 133 238 123", ".34s", "1.24s"),
    Stroke("T stem", "M291 49C284 77 278 106 273 139", ".32s", "1.55s"),
    Stroke("T bar", "M249 55C276 45 308 45 337 53", ".28s", "1.82s"),
    Stroke("underline", "M28 169C92 153 157 156 216 161C265 165 311 159 344 145", ".55s", "2.05s"),
)


def gradient_markup(identifier: str = "ink", *, compact: bool = False) -> str:
    stops = "".join(
        f'<stop{f" offset=\"{offset:g}\"" if offset else ""} stop-color="{colour}"/>'
        for offset, colour in INK_STOPS
    )
    coordinates = (
        ('24', '169', '344', '28') if compact else ('48', '220', '650', '42')
    )
    return (
        f'<linearGradient id="{identifier}" x1="{coordinates[0]}" y1="{coordinates[1]}" '
        f'x2="{coordinates[2]}" y2="{coordinates[3]}" '
        f'gradientUnits="userSpaceOnUse">{stops}</linearGradient>'
    )


def path_markup(strokes: tuple[Stroke, ...], *, animated: bool) -> str:
    paths: list[str] = []
    for index, stroke in enumerate(strokes, start=1):
        animation = ""
        if animated:
            animation = (
                ' class="signature-stroke" pathLength="1" '
                f'style="--signature-duration:{stroke.duration};--signature-delay:{stroke.delay}"'
            )
        paths.append(f'    <path{animation} d="{stroke.path}"/>')
    return "\n".join(paths)


ANIMATION_CSS = """
      .signature-stroke{stroke-dasharray:1;stroke-dashoffset:1;animation:signatureDraw var(--signature-duration) cubic-bezier(.22,.72,.25,1) var(--signature-delay) both}
      @keyframes signatureDraw{to{stroke-dashoffset:0}}
      @media(prefers-reduced-motion:reduce){.signature-stroke{animation:none!important;stroke-dashoffset:0!important}}
""".strip("\n")


def svg_document(kind: str) -> str:
    if kind == "compact":
        width, height, strokes, stroke_width = 360, 200, COMPACT_STROKES, 10.5
        title = "KC LT compact handwritten signature mark"
        desc = "A clear compact blue handwritten mark with distinct K, C, L and T initials and a low underline."
        paint = "url(#ink)"
        defs = gradient_markup(compact=True)
        animated = False
    else:
        width, height, strokes, stroke_width = 720, 260, PRIMARY_STROKES, 14
        animated = kind == "animated"
        titles = {
            "master": "KC LT handwritten signature logo",
            "animated": "Animated KC LT handwritten signature logo",
            "light": "KC LT light handwritten signature logo",
            "monochrome": "KC LT monochrome handwritten signature logo",
        }
        descriptions = {
            "master": "A transparent accessible-blue pen signature with clearly separated KC and LT initials and a low underline.",
            "animated": "A transparent accessible-blue pen signature that draws K, C, L and T once in natural stroke order, with a static reduced-motion fallback.",
            "light": "A transparent white and pale-cyan KC LT signature for dark backgrounds, with clearly separated handwritten initials.",
            "monochrome": "A transparent single-blue KC LT signature for print and restrained layouts, with clearly separated handwritten initials.",
        }
        title = titles[kind]
        desc = descriptions[kind]
        if kind in {"master", "animated"}:
            paint = "url(#ink)"
            defs = gradient_markup()
        elif kind == "light":
            paint = "url(#ink)"
            defs = (
                '<linearGradient id="ink" x1="48" y1="220" x2="650" y2="42" gradientUnits="userSpaceOnUse">'
                '<stop stop-color="#dbeafe"/><stop offset=".55" stop-color="#ffffff"/><stop offset="1" stop-color="#67e8f9"/>'
                "</linearGradient>"
            )
        else:
            paint = "#0a6fc2"
            defs = ""

    style = f"\n    <style>\n{ANIMATION_CSS}\n    </style>" if animated else ""
    defs_block = f"\n  <defs>\n    {defs}{style}\n  </defs>" if defs or style else ""
    paths = path_markup(strokes, animated=animated)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">\n'
        f'  <title id="title">{title}</title>\n'
        f'  <desc id="desc">{desc}</desc>{defs_block}\n'
        f'  <g fill="none" stroke="{paint}" stroke-width="{stroke_width:g}" '
        'stroke-linecap="round" stroke-linejoin="round">\n'
        f'{paths}\n'
        "  </g>\n"
        "</svg>\n"
    )


def banner_group(*, mobile: bool, animated: bool) -> str:
    transform = "translate(260 195) scale(.54)" if mobile else "translate(94 196) scale(.42)"
    animation = animated
    filter_attr = ' filter="url(#glow)"' if animated else ""
    paths = path_markup(COMPACT_STROKES, animated=animation).replace("    ", "")
    return (
        f'<g transform="{transform}" fill="none" stroke="url(#signatureInk)" '
        f'stroke-width="10.5" stroke-linecap="round" stroke-linejoin="round"{filter_attr}>'
        f'{paths}</g>'
    )


SIGNATURE_GROUP_RE = re.compile(
    r'<g (?=[^>]*stroke="url\(#signatureInk\)")[^>]*>.*?</g>', re.DOTALL
)
SIGNATURE_GRADIENT_RE = re.compile(
    r'<linearGradient id="signatureInk"[^>]*>.*?</linearGradient>', re.DOTALL
)
SIGNATURE_CSS_RE = re.compile(
    r'\s*/\* KC_LT_SIGNATURE_ANIMATION_START \*/.*?'
    r'/\* KC_LT_SIGNATURE_ANIMATION_END \*/',
    re.DOTALL,
)


def update_banner_source(path: Path, source: str) -> str:
    mobile = "mobile" in path.name
    animated = "animated" in path.name
    gradient = (
        '<linearGradient id="signatureInk" x1="0" y1="1" x2="1" y2="0">'
        '<stop stop-color="#155eef"/><stop offset=".52" stop-color="#0a6fc2"/>'
        '<stop offset="1" stop-color="#0b82e8"/></linearGradient>'
    )
    source, gradient_count = SIGNATURE_GRADIENT_RE.subn(gradient, source, count=1)
    if gradient_count != 1:
        raise ValueError(f"Could not find one signature gradient in {path.name}")
    source, group_count = SIGNATURE_GROUP_RE.subn(
        banner_group(mobile=mobile, animated=animated), source, count=1
    )
    if group_count != 1:
        raise ValueError(f"Could not find one signature group in {path.name}")

    source = SIGNATURE_CSS_RE.sub("", source)
    if animated:
        block = (
            "\n      /* KC_LT_SIGNATURE_ANIMATION_START */\n"
            f"{ANIMATION_CSS}\n"
            "      /* KC_LT_SIGNATURE_ANIMATION_END */\n"
        )
        source, style_count = re.subn(
            r"[ \t]*</style>", f"{block}    </style>", source, count=1
        )
        if style_count != 1:
            raise ValueError(f"Could not find the banner style block in {path.name}")
    return source


TOKEN_RE = re.compile(r"[MC]|-?\d+(?:\.\d+)?")


def flatten_path(path: str, steps_per_curve: int = 36) -> list[tuple[float, float]]:
    tokens = TOKEN_RE.findall(path)
    points: list[tuple[float, float]] = []
    index = 0
    current = (0.0, 0.0)
    command = ""
    while index < len(tokens):
        token = tokens[index]
        if token in {"M", "C"}:
            command = token
            index += 1
        if command == "M":
            current = (float(tokens[index]), float(tokens[index + 1]))
            points.append(current)
            index += 2
            command = ""
        elif command == "C":
            control1 = (float(tokens[index]), float(tokens[index + 1]))
            control2 = (float(tokens[index + 2]), float(tokens[index + 3]))
            end = (float(tokens[index + 4]), float(tokens[index + 5]))
            index += 6
            start = current
            for step in range(1, steps_per_curve + 1):
                t = step / steps_per_curve
                mt = 1.0 - t
                x = (
                    mt**3 * start[0]
                    + 3 * mt**2 * t * control1[0]
                    + 3 * mt * t**2 * control2[0]
                    + t**3 * end[0]
                )
                y = (
                    mt**3 * start[1]
                    + 3 * mt**2 * t * control1[1]
                    + 3 * mt * t**2 * control2[1]
                    + t**3 * end[1]
                )
                points.append((x, y))
            current = end
        else:
            raise ValueError(f"Unsupported path token sequence in: {path}")
    return points


def draw_disc(mask: bytearray, width: int, height: int, cx: float, cy: float, radius: float) -> None:
    left = max(0, int(math.floor(cx - radius)))
    right = min(width - 1, int(math.ceil(cx + radius)))
    top = max(0, int(math.floor(cy - radius)))
    bottom = min(height - 1, int(math.ceil(cy + radius)))
    radius_squared = radius * radius
    for y in range(top, bottom + 1):
        dy = y + 0.5 - cy
        row = y * width
        for x in range(left, right + 1):
            dx = x + 0.5 - cx
            if dx * dx + dy * dy <= radius_squared:
                mask[row + x] = 255


def raster_mask(
    width: int,
    height: int,
    strokes: tuple[Stroke, ...],
    stroke_width: float,
    supersample: int = 4,
) -> bytearray:
    high_width = width * supersample
    high_height = height * supersample
    mask = bytearray(high_width * high_height)
    radius = stroke_width * supersample / 2
    spacing = max(1.0, radius * 0.28)
    for stroke in strokes:
        points = flatten_path(stroke.path)
        scaled = [(x * supersample, y * supersample) for x, y in points]
        for start, end in zip(scaled, scaled[1:]):
            delta_x = end[0] - start[0]
            delta_y = end[1] - start[1]
            distance = math.hypot(delta_x, delta_y)
            steps = max(1, math.ceil(distance / spacing))
            for step in range(steps + 1):
                ratio = step / steps
                draw_disc(
                    mask,
                    high_width,
                    high_height,
                    start[0] + delta_x * ratio,
                    start[1] + delta_y * ratio,
                    radius,
                )

    alpha = bytearray(width * height)
    sample_area = supersample * supersample
    for y in range(height):
        for x in range(width):
            total = 0
            origin = y * supersample * high_width + x * supersample
            for sample_y in range(supersample):
                row = origin + sample_y * high_width
                total += sum(mask[row : row + supersample])
            alpha[y * width + x] = round(total / sample_area)
    return alpha


def interpolate_ink(x_ratio: float) -> tuple[int, int, int]:
    if x_ratio <= INK_STOPS[1][0]:
        local = x_ratio / INK_STOPS[1][0]
        start, end = INK_RGB[0], INK_RGB[1]
    else:
        local = (x_ratio - INK_STOPS[1][0]) / (1 - INK_STOPS[1][0])
        start, end = INK_RGB[1], INK_RGB[2]
    return tuple(round(a + (b - a) * local) for a, b in zip(start, end))


def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + chunk_type
        + data
        + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    )


def render_png(
    width: int,
    height: int,
    strokes: tuple[Stroke, ...],
    stroke_width: float,
) -> bytes:
    alpha = raster_mask(width, height, strokes, stroke_width)
    raw = bytearray()
    colours = [interpolate_ink(x / max(1, width - 1)) for x in range(width)]
    for y in range(height):
        raw.append(0)
        for x in range(width):
            pixel_alpha = alpha[y * width + x]
            if pixel_alpha:
                red, green, blue = colours[x]
                raw.extend((red, green, blue, pixel_alpha))
            else:
                raw.extend((0, 0, 0, 0))
    signature = b"\x89PNG\r\n\x1a\n"
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (
        signature
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", zlib.compress(bytes(raw), level=9))
        + png_chunk(b"IEND", b"")
    )


def expected_outputs() -> dict[Path, bytes]:
    outputs: dict[Path, bytes] = {
        BRAND_DIR / "kc-lt-signature.svg": svg_document("master").encode(),
        BRAND_DIR / "kc-lt-signature-animated.svg": svg_document("animated").encode(),
        BRAND_DIR / "kc-lt-signature-compact.svg": svg_document("compact").encode(),
        BRAND_DIR / "kc-lt-signature-light.svg": svg_document("light").encode(),
        BRAND_DIR / "kc-lt-signature-monochrome.svg": svg_document("monochrome").encode(),
        BRAND_DIR / "kc-lt-signature.png": render_png(720, 260, PRIMARY_STROKES, 14),
        BRAND_DIR / "kc-lt-signature-compact.png": render_png(360, 200, COMPACT_STROKES, 10.5),
    }
    for path in BANNER_FILES:
        source = path.read_text(encoding="utf-8-sig")
        outputs[path] = update_banner_source(path, source).encode()
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify that every generated signature asset is current without writing.",
    )
    args = parser.parse_args()

    outputs = expected_outputs()
    stale: list[Path] = []
    for path, content in outputs.items():
        if not path.exists() or path.read_bytes() != content:
            stale.append(path)
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)

    if args.check and stale:
        for path in stale:
            print(f"STALE {path.relative_to(ROOT)}")
        return 1
    action = "Verified" if args.check else "Generated"
    print(f"{action} {len(outputs)} KC x LT signature assets and embeddings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
