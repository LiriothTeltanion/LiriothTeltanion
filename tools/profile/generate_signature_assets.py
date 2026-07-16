#!/usr/bin/env python3
"""Generate the canonical KC star LT signature assets and visual embeddings.

The public mark is intentionally built from explicit cubic Bezier strokes rather
than a font.  This keeps the four initials recognisable, the animation order
predictable, and every exported asset independent of installed typefaces.  A
separate four-point star marks the pen lift between KC and LT without changing
the eight canonical handwriting strokes.
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
SOCIAL_DIR = ROOT / "assets" / "social"
BANNER_FILES = (
    ROOT / "assets" / "profile-banner-animated.svg",
    ROOT / "assets" / "profile-banner-static.svg",
    ROOT / "assets" / "profile-banner-mobile-animated.svg",
    ROOT / "assets" / "profile-banner-mobile-static.svg",
)
SOCIAL_FILES = tuple(sorted(SOCIAL_DIR.glob("*-social-preview.svg")))

INK_STOPS = ((0.0, "#155eef"), (0.52, "#0a6fc2"), (1.0, "#0b82e8"))
INK_RGB = ((21, 94, 239), (10, 111, 194), (11, 130, 232))
STAR_CORE = "#eff6ff"
STAR_MID = "#60a5fa"
STAR_OUTER = "#2563eb"
STAR_GLOW = "#3b82f6"
STAR_GLOW_OPACITY = 0.38


@dataclass(frozen=True)
class Stroke:
    name: str
    path: str
    duration: str
    delay: str


@dataclass(frozen=True)
class StarSpec:
    """Geometry and glow contract for one KC star LT export size."""

    center_x: float
    center_y: float
    width: float
    height: float
    blur: float


# The star behaves like the luminous punctuation point in KC.LT: centered in
# the pen lift, lowered toward the baseline, and large enough to survive the
# compact banner/social-card transforms without competing with the initials.
FULL_STAR = StarSpec(348, 148, 24, 28, 4.0)
COMPACT_STAR = StarSpec(180, 120, 16, 20, 2.6)


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


def star_path(width: float, height: float) -> str:
    """Return a centered four-point star path with the requested outer size."""

    half_width = width / 2
    half_height = height / 2
    inner_x = width * 0.14
    inner_y = height * 0.14
    return (
        f"M0 {-half_height:g}L{inner_x:g} {-inner_y:g}L{half_width:g} 0"
        f"L{inner_x:g} {inner_y:g}L0 {half_height:g}L{-inner_x:g} {inner_y:g}"
        f"L{-half_width:g} 0L{-inner_x:g} {-inner_y:g}Z"
    )


def star_filter_markup(identifier: str, blur: float) -> str:
    """Return a luminous blue halo that preserves the crisp three-tone star."""

    return (
        f'<filter id="{identifier}" x="-100%" y="-100%" width="300%" height="300%" '
        'color-interpolation-filters="sRGB">'
        f'<feGaussianBlur in="SourceGraphic" stdDeviation="{blur:g}" result="starBlur"/>'
        f'<feFlood flood-color="{STAR_GLOW}" flood-opacity="{STAR_GLOW_OPACITY:g}" '
        'result="starColour"/>'
        '<feComposite in="starColour" in2="starBlur" operator="in" result="starGlow"/>'
        '<feMerge><feMergeNode in="starGlow"/><feMergeNode in="SourceGraphic"/></feMerge>'
        '</filter>'
    )


def star_markup(
    spec: StarSpec,
    *,
    filter_id: str | None,
    monochrome: bool = False,
    wrapper_transform: str | None = None,
) -> str:
    """Render exactly one separate star group after the eight pen strokes."""

    path = star_path(spec.width, spec.height)
    outer_filter = f' filter="url(#{filter_id})"' if filter_id else ""
    if monochrome:
        shapes = f'<path d="{path}" fill="#0a6fc2"/>'
    else:
        shapes = (
            f'<path d="{path}" fill="{STAR_OUTER}"/>'
            f'<path d="{path}" fill="{STAR_MID}" transform="scale(.64)"/>'
            f'<path d="{path}" fill="{STAR_CORE}" transform="scale(.28)"/>'
        )
    star = (
        f'<g class="signature-star-placement" '
        f'transform="translate({spec.center_x:g} {spec.center_y:g})">'
        f'<g class="signature-star" aria-hidden="true"{outer_filter}>{shapes}</g></g>'
    )
    if wrapper_transform:
        return f'<g transform="{wrapper_transform}" aria-hidden="true">{star}</g>'
    return star


ANIMATION_CSS = """
      .signature-stroke{stroke-dasharray:1;stroke-dashoffset:1;animation:signatureDraw var(--signature-duration) cubic-bezier(.22,.72,.25,1) var(--signature-delay) both}
      .signature-star{opacity:0;animation:signatureStarReveal .32s ease-out 1.14s both}
      @keyframes signatureDraw{to{stroke-dashoffset:0}}
      @keyframes signatureStarReveal{from{opacity:0}to{opacity:1}}
      @media(prefers-reduced-motion:reduce){.signature-stroke{animation:none!important;stroke-dashoffset:0!important}.signature-star{animation:none!important;opacity:1!important}}
""".strip("\n")


def svg_document(kind: str) -> str:
    if kind == "compact":
        width, height, strokes, stroke_width = 360, 200, COMPACT_STROKES, 10.5
        star_spec = COMPACT_STAR
        title = "KC ✦ LT compact handwritten signature mark"
        desc = "A clear compact blue KC star LT handwritten mark with distinct K, C, L and T initials, a larger luminous four-point star lowered like a pen-dot and a low underline."
        paint = "url(#ink)"
        defs = gradient_markup(compact=True) + star_filter_markup("starGlow", star_spec.blur)
        animated = False
        monochrome = False
    else:
        width, height, strokes, stroke_width = 720, 260, PRIMARY_STROKES, 14
        star_spec = FULL_STAR
        animated = kind == "animated"
        monochrome = kind == "monochrome"
        titles = {
            "master": "KC ✦ LT handwritten signature logo",
            "animated": "Animated KC ✦ LT handwritten signature logo",
            "light": "KC ✦ LT light handwritten signature logo",
            "monochrome": "KC ✦ LT monochrome handwritten signature logo",
        }
        descriptions = {
            "master": "A transparent accessible-blue KC star LT pen signature with clearly separated initials, a larger lowered glowing four-point star and a low underline.",
            "animated": "A transparent accessible-blue KC star LT signature that draws eight pen strokes and reveals one larger lowered glowing four-point star once, with a static reduced-motion fallback.",
            "light": "A transparent light KC star LT signature for dark backgrounds, with clearly separated handwritten initials and a larger lowered glowing four-point star.",
            "monochrome": "A transparent single-blue KC star LT signature for print and restrained layouts, with clearly separated initials and one unblurred four-point star.",
        }
        title = titles[kind]
        desc = descriptions[kind]
        if kind in {"master", "animated"}:
            paint = "url(#ink)"
            defs = gradient_markup() + star_filter_markup("starGlow", star_spec.blur)
        elif kind == "light":
            paint = "url(#ink)"
            defs = (
                '<linearGradient id="ink" x1="48" y1="220" x2="650" y2="42" gradientUnits="userSpaceOnUse">'
                '<stop stop-color="#dbeafe"/><stop offset=".55" stop-color="#ffffff"/><stop offset="1" stop-color="#67e8f9"/>'
                "</linearGradient>"
            ) + star_filter_markup("starGlow", star_spec.blur)
        else:
            paint = "#0a6fc2"
            defs = ""

    style = f"\n    <style>\n{ANIMATION_CSS}\n    </style>" if animated else ""
    defs_block = f"\n  <defs>\n    {defs}{style}\n  </defs>" if defs or style else ""
    paths = path_markup(strokes, animated=animated)
    star = star_markup(
        star_spec,
        filter_id=None if monochrome else "starGlow",
        monochrome=monochrome,
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">\n'
        f'  <title id="title">{title}</title>\n'
        f'  <desc id="desc">{desc}</desc>{defs_block}\n'
        f'  <g class="signature-ink" fill="none" stroke="{paint}" stroke-width="{stroke_width:g}" '
        'stroke-linecap="round" stroke-linejoin="round">\n'
        f'{paths}\n'
        "  </g>\n"
        f"  {star}\n"
        "</svg>\n"
    )


def banner_group(*, mobile: bool, animated: bool) -> str:
    transform = "translate(260 195) scale(.54)" if mobile else "translate(94 196) scale(.42)"
    animation = animated
    filter_attr = ' filter="url(#glow)"' if animated else ""
    paths = path_markup(COMPACT_STROKES, animated=animation).replace("    ", "")
    return (
        f'<g class="signature-ink" transform="{transform}" fill="none" stroke="url(#signatureInk)" '
        f'stroke-width="10.5" stroke-linecap="round" stroke-linejoin="round"{filter_attr}>'
        f'{paths}</g>'
    )


STAR_EMBED_RE = re.compile(
    r"\s*<!-- KC_LT_STAR_START -->.*?<!-- KC_LT_STAR_END -->", re.DOTALL
)
STAR_FILTER_EMBED_RE = re.compile(
    r"\s*<!-- KC_LT_STAR_FILTER_START -->.*?<!-- KC_LT_STAR_FILTER_END -->",
    re.DOTALL,
)


def embedded_star_block(transform: str, *, filter_id: str = "signatureStarGlow") -> str:
    return (
        "\n  <!-- KC_LT_STAR_START -->\n  "
        + star_markup(
            COMPACT_STAR,
            filter_id=filter_id,
            wrapper_transform=transform,
        )
        + "\n  <!-- KC_LT_STAR_END -->"
    )


def embedded_star_filter_block(*, filter_id: str = "signatureStarGlow") -> str:
    return (
        "\n    <!-- KC_LT_STAR_FILTER_START -->"
        + star_filter_markup(filter_id, COMPACT_STAR.blur)
        + "<!-- KC_LT_STAR_FILTER_END -->"
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
    source = STAR_EMBED_RE.sub("", source)
    source = STAR_FILTER_EMBED_RE.sub("", source)
    gradient = (
        '<linearGradient id="signatureInk" x1="0" y1="1" x2="1" y2="0">'
        '<stop stop-color="#155eef"/><stop offset=".52" stop-color="#0a6fc2"/>'
        '<stop offset="1" stop-color="#0b82e8"/></linearGradient>'
    )
    source, gradient_count = SIGNATURE_GRADIENT_RE.subn(gradient, source, count=1)
    if gradient_count != 1:
        raise ValueError(f"Could not find one signature gradient in {path.name}")
    source = source.replace(
        gradient,
        gradient + embedded_star_filter_block(),
        1,
    )
    transform = "translate(260 195) scale(.54)" if mobile else "translate(94 196) scale(.42)"
    replacement = banner_group(mobile=mobile, animated=animated) + embedded_star_block(transform)
    source, group_count = SIGNATURE_GROUP_RE.subn(
        replacement, source, count=1
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
    source = source.replace(
        "a blue KC LT handwritten signature",
        "a blue KC star LT handwritten signature",
    )
    return source


SOCIAL_SIGNATURE_GROUP_RE = re.compile(
    r'<g (?P<attributes>[^>]*)>\s*<path d="'
    + re.escape(COMPACT_STROKES[0].path)
    + r'"/>.*?</g>',
    re.DOTALL,
)


def update_social_source(path: Path, source: str) -> str:
    """Embed the canonical compact star without altering each card's layout."""

    source = STAR_EMBED_RE.sub("", source)
    source = STAR_FILTER_EMBED_RE.sub("", source)
    match = SOCIAL_SIGNATURE_GROUP_RE.search(source)
    if match is None:
        raise ValueError(f"Could not find the compact signature group in {path.name}")
    attributes = match.group("attributes")
    if 'class="signature-ink"' not in attributes:
        attributes = 'class="signature-ink" ' + attributes
    transform_match = re.search(r'transform="([^"]+)"', attributes)
    if transform_match is None:
        raise ValueError(f"Could not find the signature transform in {path.name}")
    pen_paths = path_markup(COMPACT_STROKES, animated=False)
    pen_group = f'<g {attributes}>\n{pen_paths}\n  </g>'
    replacement = pen_group + embedded_star_block(transform_match.group(1))
    source = source[: match.start()] + replacement + source[match.end() :]
    source = source.replace(
        "</defs>", embedded_star_filter_block() + "\n  </defs>", 1
    )

    def enrich_description(description_match: re.Match[str]) -> str:
        description = description_match.group(1).strip()
        if "KC star LT" not in description:
            description = description.rstrip(".") + ". The card includes the KC star LT signature."
        return f'<desc id="desc">{description}</desc>'

    source = re.sub(
        r'<desc id="desc">(.*?)</desc>',
        enrich_description,
        source,
        count=1,
        flags=re.DOTALL,
    )
    source = source.replace("KC × LT", "KC ✦ LT")
    had_final_newline = source.endswith("\n")
    source = "\n".join(line.rstrip() for line in source.splitlines())
    return source + ("\n" if had_final_newline else "")


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


def star_polygon(spec: StarSpec, scale: float = 1.0) -> list[tuple[float, float]]:
    """Return absolute raster points for one scaled four-point star layer."""

    half_width = spec.width * scale / 2
    half_height = spec.height * scale / 2
    inner_x = spec.width * scale * 0.14
    inner_y = spec.height * scale * 0.14
    cx, cy = spec.center_x, spec.center_y
    return [
        (cx, cy - half_height),
        (cx + inner_x, cy - inner_y),
        (cx + half_width, cy),
        (cx + inner_x, cy + inner_y),
        (cx, cy + half_height),
        (cx - inner_x, cy + inner_y),
        (cx - half_width, cy),
        (cx - inner_x, cy - inner_y),
    ]


def point_in_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    """Return whether a point is inside a simple polygon."""

    x, y = point
    inside = False
    previous = polygon[-1]
    for current in polygon:
        x1, y1 = previous
        x2, y2 = current
        if (y1 > y) != (y2 > y):
            intersection_x = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < intersection_x:
                inside = not inside
        previous = current
    return inside


def point_segment_distance(
    point: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
) -> float:
    """Return the shortest distance from a point to a line segment."""

    delta_x = end[0] - start[0]
    delta_y = end[1] - start[1]
    length_squared = delta_x * delta_x + delta_y * delta_y
    if length_squared == 0:
        return math.hypot(point[0] - start[0], point[1] - start[1])
    ratio = (
        (point[0] - start[0]) * delta_x + (point[1] - start[1]) * delta_y
    ) / length_squared
    ratio = max(0.0, min(1.0, ratio))
    closest = (start[0] + delta_x * ratio, start[1] + delta_y * ratio)
    return math.hypot(point[0] - closest[0], point[1] - closest[1])


def composite_pixel(
    pixels: bytearray,
    offset: int,
    colour: tuple[int, int, int],
    alpha: int,
) -> None:
    """Alpha-composite one straight-alpha RGBA pixel."""

    if alpha <= 0:
        return
    source_alpha = alpha / 255
    destination_alpha = pixels[offset + 3] / 255
    output_alpha = source_alpha + destination_alpha * (1 - source_alpha)
    if output_alpha == 0:
        return
    for channel in range(3):
        destination = pixels[offset + channel]
        value = (
            colour[channel] * source_alpha
            + destination * destination_alpha * (1 - source_alpha)
        ) / output_alpha
        pixels[offset + channel] = round(value)
    pixels[offset + 3] = round(output_alpha * 255)


def paint_polygon(
    pixels: bytearray,
    width: int,
    height: int,
    polygon: list[tuple[float, float]],
    colour: tuple[int, int, int],
    supersample: int = 4,
) -> None:
    """Paint a small anti-aliased polygon onto a transparent RGBA canvas."""

    left = max(0, math.floor(min(point[0] for point in polygon)) - 1)
    right = min(width - 1, math.ceil(max(point[0] for point in polygon)) + 1)
    top = max(0, math.floor(min(point[1] for point in polygon)) - 1)
    bottom = min(height - 1, math.ceil(max(point[1] for point in polygon)) + 1)
    total_samples = supersample * supersample
    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            covered = 0
            for sample_y in range(supersample):
                for sample_x in range(supersample):
                    point = (
                        x + (sample_x + 0.5) / supersample,
                        y + (sample_y + 0.5) / supersample,
                    )
                    covered += point_in_polygon(point, polygon)
            alpha = round(255 * covered / total_samples)
            composite_pixel(pixels, (y * width + x) * 4, colour, alpha)


def paint_star(pixels: bytearray, width: int, height: int, spec: StarSpec) -> None:
    """Paint the three-tone punctuation star and its luminous blue halo."""

    outer = star_polygon(spec)
    glow_radius = spec.blur * 3
    left = max(0, math.floor(spec.center_x - spec.width / 2 - glow_radius))
    right = min(width - 1, math.ceil(spec.center_x + spec.width / 2 + glow_radius))
    top = max(0, math.floor(spec.center_y - spec.height / 2 - glow_radius))
    bottom = min(height - 1, math.ceil(spec.center_y + spec.height / 2 + glow_radius))
    edges = list(zip(outer, outer[1:] + outer[:1]))
    glow_colour = (59, 130, 246)
    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            point = (x + 0.5, y + 0.5)
            if point_in_polygon(point, outer):
                distance = 0.0
            else:
                distance = min(
                    point_segment_distance(point, start, end) for start, end in edges
                )
            alpha = round(
                255
                * STAR_GLOW_OPACITY
                * math.exp(-(distance * distance) / (2 * spec.blur * spec.blur))
            )
            composite_pixel(pixels, (y * width + x) * 4, glow_colour, alpha)

    paint_polygon(pixels, width, height, outer, (37, 99, 235))
    paint_polygon(pixels, width, height, star_polygon(spec, 0.64), (96, 165, 250))
    paint_polygon(pixels, width, height, star_polygon(spec, 0.28), (239, 246, 255))


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
    star_spec: StarSpec,
) -> bytes:
    alpha = raster_mask(width, height, strokes, stroke_width)
    pixels = bytearray(width * height * 4)
    colours = [interpolate_ink(x / max(1, width - 1)) for x in range(width)]
    for y in range(height):
        for x in range(width):
            pixel_alpha = alpha[y * width + x]
            offset = (y * width + x) * 4
            if pixel_alpha:
                red, green, blue = colours[x]
                pixels[offset : offset + 4] = bytes((red, green, blue, pixel_alpha))
    paint_star(pixels, width, height, star_spec)

    raw = bytearray()
    row_width = width * 4
    for y in range(height):
        raw.append(0)
        raw.extend(pixels[y * row_width : (y + 1) * row_width])
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
        BRAND_DIR / "kc-lt-signature.png": render_png(
            720, 260, PRIMARY_STROKES, 14, FULL_STAR
        ),
        BRAND_DIR / "kc-lt-signature-compact.png": render_png(
            360, 200, COMPACT_STROKES, 10.5, COMPACT_STAR
        ),
    }
    for path in BANNER_FILES:
        source = path.read_text(encoding="utf-8-sig")
        outputs[path] = update_banner_source(path, source).encode()
    for path in SOCIAL_FILES:
        source = path.read_text(encoding="utf-8-sig")
        outputs[path] = update_social_source(path, source).encode()
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
    print(f"{action} {len(outputs)} KC star LT signature assets and embeddings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
