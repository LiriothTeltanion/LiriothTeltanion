"""Generate Kevin Cusnir's responsive world-journey SVG assets.

The generator uses the public-domain Natural Earth v5.1.1 Admin-0 country
polygons plus its tiny-country point layer. Geometry is projected with a
compact Robinson-style projection and quantized to 0.1 SVG units so the
result remains self-contained and suitable for a GitHub profile README.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "assets"
VERSION = "v5.1.1"
DEFAULT_CACHE = ROOT / ".cache" / "profile" / f"natural-earth-{VERSION}"
SOURCE_ROOT = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    f"{VERSION}/geojson"
)
COUNTRIES_URL = f"{SOURCE_ROOT}/ne_110m_admin_0_countries.geojson"
TINY_COUNTRIES_URL = f"{SOURCE_ROOT}/ne_110m_admin_0_tiny_countries.geojson"
MAX_SVG_BYTES = 512 * 1024

SAN_CRISTOBAL = (-72.2250, 7.7670)
BEERSHEBA = (34.7913, 31.2518)

# Robinson projection lookup coefficients at five-degree latitude intervals.
ROBINSON_X = (
    1.0000,
    0.9986,
    0.9954,
    0.9900,
    0.9822,
    0.9730,
    0.9600,
    0.9427,
    0.9216,
    0.8962,
    0.8679,
    0.8350,
    0.7986,
    0.7597,
    0.7186,
    0.6732,
    0.6213,
    0.5722,
    0.5322,
)
ROBINSON_Y = (
    0.0000,
    0.0620,
    0.1240,
    0.1860,
    0.2480,
    0.3100,
    0.3720,
    0.4340,
    0.4958,
    0.5571,
    0.6176,
    0.6769,
    0.7346,
    0.7903,
    0.8435,
    0.8936,
    0.9394,
    0.9761,
    1.0000,
)


@dataclass(frozen=True)
class MapBox:
    """Projected map placement inside an SVG view box."""

    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True)
class SourceSpec:
    """Pinned Natural Earth source and its verified byte checksum."""

    filename: str
    url: str
    sha256: str


@dataclass(frozen=True)
class MapMarkup:
    """Pre-rendered geometry and route coordinates for one layout."""

    outline: str
    graticule: str
    countries: str
    tiny_countries: str
    route: str
    origin: tuple[float, float]
    current: tuple[float, float]
    country_count: int
    tiny_count: int


COUNTRIES_SOURCE = SourceSpec(
    filename="ne_110m_admin_0_countries.geojson",
    url=COUNTRIES_URL,
    sha256="6866c877d39cba9c357620878839b336d569f8c662d3cfab4cb1dbe2d39c977f",
)
TINY_COUNTRIES_SOURCE = SourceSpec(
    filename="ne_110m_admin_0_tiny_countries.geojson",
    url=TINY_COUNTRIES_URL,
    sha256="753c4b167361f0f1223091d52f98aaddfb9101529eef263cc094057e43228c40",
)


def build_parser() -> argparse.ArgumentParser:
    """Return the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Generate responsive Natural Earth world-journey SVG assets."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Destination directory for the four SVG assets.",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=DEFAULT_CACHE,
        help="Verified local cache for the pinned Natural Earth GeoJSON files.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Require verified cached sources and make no network request.",
    )
    parser.add_argument(
        "--refresh-cache",
        action="store_true",
        help="Download and re-verify pinned sources even when the cache is valid.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare generated SVG text with existing outputs without writing assets.",
    )
    return parser


def _decode_verified_geojson(payload: bytes, source: SourceSpec) -> dict[str, Any]:
    """Validate source bytes against provenance before decoding GeoJSON."""
    digest = hashlib.sha256(payload).hexdigest()
    if digest != source.sha256:
        raise ValueError(
            f"Checksum mismatch for {source.filename}: expected {source.sha256}, got {digest}."
        )
    data = json.loads(payload.decode("utf-8"))
    if data.get("type") != "FeatureCollection" or not data.get("features"):
        raise ValueError(f"Unexpected GeoJSON payload from {source.url}")
    return data


def fetch_geojson(
    source: SourceSpec,
    cache_dir: Path = DEFAULT_CACHE,
    *,
    offline: bool = False,
    refresh_cache: bool = False,
) -> dict[str, Any]:
    """Load a checksum-verified pinned source from cache or the network."""
    cache_path = cache_dir / source.filename
    if cache_path.exists() and not refresh_cache:
        try:
            return _decode_verified_geojson(cache_path.read_bytes(), source)
        except (OSError, UnicodeError, ValueError):
            if offline:
                raise
            print(f"Ignoring invalid cache entry: {cache_path}")

    if offline:
        raise FileNotFoundError(
            f"Verified offline source unavailable: {cache_path}. Run once without --offline."
        )

    request = urllib.request.Request(
        source.url,
        headers={"User-Agent": "Lirioth-profile-map/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = response.read()
    data = _decode_verified_geojson(payload, source)

    cache_dir.mkdir(parents=True, exist_ok=True)
    temporary = cache_path.with_suffix(cache_path.suffix + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(cache_path)
    return data


def _interpolate(values: Sequence[float], latitude: float) -> float:
    """Interpolate one Robinson coefficient for a latitude."""
    absolute = min(abs(latitude), 90.0)
    if absolute >= 90.0:
        return values[-1]
    index = int(absolute // 5.0)
    fraction = (absolute - index * 5.0) / 5.0
    return values[index] + (values[index + 1] - values[index]) * fraction


def project(lon: float, lat: float, box: MapBox) -> tuple[float, float]:
    """Project longitude/latitude into a compact Robinson-style map box."""
    x_coefficient = _interpolate(ROBINSON_X, lat)
    y_coefficient = _interpolate(ROBINSON_Y, lat)
    normalized_x = (lon / 180.0) * x_coefficient
    normalized_y = math.copysign(y_coefficient, -lat) if lat else 0.0
    return (
        box.x + ((normalized_x + 1.0) / 2.0) * box.width,
        box.y + ((normalized_y + 1.0) / 2.0) * box.height,
    )


def _fmt(value: float) -> str:
    """Quantize coordinates while avoiding negative zero."""
    rounded = round(value, 1)
    if rounded == 0:
        rounded = 0.0
    return f"{rounded:.1f}".rstrip("0").rstrip(".")


def _path_from_points(points: Iterable[tuple[float, float]], close: bool = False) -> str:
    """Encode projected points as compact SVG path data."""
    cleaned: list[tuple[float, float]] = []
    for point in points:
        quantized = (round(point[0], 1), round(point[1], 1))
        if not cleaned or quantized != cleaned[-1]:
            cleaned.append(quantized)
    if not cleaned:
        return ""
    commands = [f"M{_fmt(cleaned[0][0])} {_fmt(cleaned[0][1])}"]
    commands.extend(f"L{_fmt(x)} {_fmt(y)}" for x, y in cleaned[1:])
    if close:
        commands.append("Z")
    return "".join(commands)


def _geometry_rings(geometry: Mapping[str, Any]) -> Iterable[Sequence[Sequence[float]]]:
    """Yield polygon rings from Polygon or MultiPolygon geometry."""
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates", [])
    if geometry_type == "Polygon":
        yield from coordinates
    elif geometry_type == "MultiPolygon":
        for polygon in coordinates:
            yield from polygon
    else:
        raise ValueError(f"Unsupported country geometry: {geometry_type}")


def _slug(value: str) -> str:
    """Return a stable lowercase CSS/ID token."""
    token = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return token or "unknown"


def _world_outline(box: MapBox) -> str:
    """Build the curved Robinson world boundary."""
    right = [project(180.0, lat, box) for lat in range(90, -91, -3)]
    left = [project(-180.0, lat, box) for lat in range(-90, 91, 3)]
    return _path_from_points([*right, *left], close=True)


def _graticule(box: MapBox) -> str:
    """Build latitude and longitude guide paths."""
    paths: list[str] = []
    for latitude in (-60, -30, 0, 30, 60):
        points = [project(lon, float(latitude), box) for lon in range(-180, 181, 5)]
        paths.append(_path_from_points(points))
    for longitude in (-150, -120, -90, -60, -30, 0, 30, 60, 90, 120, 150):
        points = [project(float(longitude), lat, box) for lat in range(-90, 91, 3)]
        paths.append(_path_from_points(points))
    return "".join(f'<path d="{path}"/>' for path in paths)


def build_map_markup(
    countries_data: Mapping[str, Any],
    tiny_data: Mapping[str, Any],
    box: MapBox,
) -> MapMarkup:
    """Render all country polygons, tiny-country points, and the life route."""
    country_paths: list[str] = []
    features = countries_data["features"]
    for feature in sorted(features, key=lambda item: item["properties"].get("ADMIN", "")):
        properties = feature["properties"]
        name = str(properties.get("ADMIN") or properties.get("NAME_EN") or "Unknown")
        iso = str(properties.get("ADM0_A3") or properties.get("ISO_A3") or "---")
        continent = _slug(str(properties.get("CONTINENT") or "Other"))
        ring_paths: list[str] = []
        for ring in _geometry_rings(feature["geometry"]):
            points = [project(float(lon), float(lat), box) for lon, lat, *_ in ring]
            path = _path_from_points(points, close=True)
            if path:
                ring_paths.append(path)
        classes = ["country", f"continent-{continent}"]
        if iso == "VEN":
            classes.append("origin-country")
        elif iso == "ISR":
            classes.append("current-country")
        country_paths.append(
            '<path data-layer="country" '
            f'data-iso="{html.escape(iso, quote=True)}" '
            f'data-country="{html.escape(name, quote=True)}" '
            f'class="{" ".join(classes)}" fill-rule="evenodd" d="{"".join(ring_paths)}"/>'
        )

    tiny_markers: list[str] = []
    for index, feature in enumerate(tiny_data["features"]):
        properties = feature["properties"]
        name = str(properties.get("ADMIN") or properties.get("NAME_EN") or "Tiny country")
        iso = str(properties.get("ADM0_A3") or properties.get("ISO_A3") or "---")
        lon, lat, *_ = feature["geometry"]["coordinates"]
        x, y = project(float(lon), float(lat), box)
        classes = ["tiny-country"]
        if iso == "VEN":
            classes.append("origin-country")
        elif iso == "ISR":
            classes.append("current-country")
        tiny_markers.append(
            '<circle data-layer="tiny-country" '
            f'data-iso="{html.escape(iso, quote=True)}" '
            f'data-country="{html.escape(name, quote=True)}" '
            f'data-index="{index}" class="{" ".join(classes)}" '
            f'cx="{_fmt(x)}" cy="{_fmt(y)}" r="1.8"/>'
        )

    origin = project(*SAN_CRISTOBAL, box)
    current = project(*BEERSHEBA, box)
    control_x = (origin[0] + current[0]) / 2.0
    control_y = min(origin[1], current[1]) - box.height * 0.19
    route = (
        f"M{_fmt(origin[0])} {_fmt(origin[1])}"
        f"Q{_fmt(control_x)} {_fmt(control_y)} {_fmt(current[0])} {_fmt(current[1])}"
    )
    return MapMarkup(
        outline=_world_outline(box),
        graticule=_graticule(box),
        countries="".join(country_paths),
        tiny_countries="".join(tiny_markers),
        route=route,
        origin=origin,
        current=current,
        country_count=len(features),
        tiny_count=len(tiny_markers),
    )


def _styles(animated: bool) -> str:
    """Return shared SVG styling plus optional motion."""
    animation = ""
    if animated:
        animation = """
      .route-flow{animation:route-flow 4.8s linear infinite}
      .route-spark{animation:route-spark 4.8s linear infinite}
      .origin-halo,.current-halo{animation:halo 3.2s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
      .current-halo{animation-delay:.8s}.scan{animation:scan 8s ease-in-out infinite}
      .map-glow{animation:glow 6s ease-in-out infinite}
      @keyframes route-flow{to{stroke-dashoffset:-84}}
      @keyframes route-spark{to{stroke-dashoffset:-260}}
      @keyframes halo{50%{opacity:.28;transform:scale(1.35)}}
      @keyframes scan{0%,12%{transform:translateX(-180px);opacity:0}45%,58%{opacity:.42}88%,100%{transform:translateX(760px);opacity:0}}
      @keyframes glow{50%{opacity:.74}}
      @media(prefers-reduced-motion:reduce){.route-flow,.route-spark,.origin-halo,.current-halo,.scan,.map-glow{animation:none!important}}
"""
    return (
        """
      .title{font:800 38px system-ui,"Segoe UI",sans-serif;fill:#f2fbff}.eyebrow{font:800 16px system-ui,"Segoe UI",sans-serif;fill:#67e8f9;letter-spacing:3px}.subtitle{font:600 18px system-ui,"Segoe UI",sans-serif;fill:#a9bdcd}
      .card-title{font:800 22px system-ui,"Segoe UI",sans-serif;fill:#f2fbff}.card-kicker{font:800 13px system-ui,"Segoe UI",sans-serif;letter-spacing:2px}.card-copy{font:600 15px system-ui,"Segoe UI",sans-serif;fill:#a9bdcd}.chip{font:800 13px system-ui,"Segoe UI",sans-serif;fill:#dff8ff}.micro{font:700 11px system-ui,"Segoe UI",sans-serif;fill:#8ba8b8;letter-spacing:1.1px}
      .country{fill:#12384c;stroke:#8cecff;stroke-opacity:.45;stroke-width:.65;vector-effect:non-scaling-stroke}.continent-africa{fill:#164557}.continent-asia{fill:#173c59}.continent-europe{fill:#1d405e}.continent-north-america{fill:#123f4b}.continent-south-america{fill:#174a4b}.continent-oceania{fill:#253c62}.continent-seven-seas-open-ocean{fill:#1b3a50}.origin-country{fill:#d99a21;stroke:#fde68a;stroke-opacity:.95}.current-country{fill:#8b6bd6;stroke:#ddd6fe;stroke-opacity:.95}
      .tiny-country{fill:#8cecff;stroke:#071727;stroke-width:.6}.tiny-country.origin-country{fill:#fbbf24}.tiny-country.current-country{fill:#c4b5fd}
      .graticule{fill:none;stroke:#7dd3fc;stroke-opacity:.16;stroke-width:.7;vector-effect:non-scaling-stroke}.route-base{fill:none;stroke:url(#route);stroke-width:4;stroke-linecap:round}.route-flow{fill:none;stroke:#f8fbff;stroke-width:1.6;stroke-dasharray:8 10;stroke-linecap:round}.route-spark{fill:none;stroke:#fff7c2;stroke-width:5;stroke-dasharray:1 259;stroke-linecap:round}.origin-dot{fill:#fbbf24}.current-dot{fill:#c4b5fd}.origin-halo{fill:none;stroke:#fbbf24;stroke-width:3}.current-halo{fill:none;stroke:#c4b5fd;stroke-width:3}
"""
        + animation
    )


def _defs(markup: MapMarkup, animated: bool, suffix: str) -> str:
    """Return gradients, clip path, and styling for one asset."""
    return f"""
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#06101e"/><stop offset=".55" stop-color="#0b2633"/><stop offset="1" stop-color="#211241"/></linearGradient>
    <linearGradient id="ocean" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#071d30"/><stop offset=".52" stop-color="#0b3145"/><stop offset="1" stop-color="#14213e"/></linearGradient>
    <linearGradient id="route" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#fbbf24"/><stop offset=".55" stop-color="#22d3ee"/><stop offset="1" stop-color="#c4b5fd"/></linearGradient>
    <linearGradient id="scan-gradient" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#67e8f9" stop-opacity="0"/><stop offset=".5" stop-color="#67e8f9" stop-opacity=".55"/><stop offset="1" stop-color="#67e8f9" stop-opacity="0"/></linearGradient>
    <radialGradient id="map-glow"><stop stop-color="#22d3ee" stop-opacity=".22"/><stop offset="1" stop-color="#22d3ee" stop-opacity="0"/></radialGradient>
    <pattern id="stars" width="84" height="62" patternUnits="userSpaceOnUse"><circle cx="13" cy="14" r="1" fill="#d9f7ff" opacity=".28"/><circle cx="64" cy="41" r="1.2" fill="#c4b5fd" opacity=".24"/></pattern>
    <clipPath id="world-clip-{suffix}"><path d="{markup.outline}"/></clipPath>
    <style>{_styles(animated)}</style>
  </defs>"""


def _map_layer(markup: MapMarkup, suffix: str, animated: bool) -> str:
    """Return the complete projected country map and life-route overlay."""
    ox, oy = markup.origin
    cx, cy = markup.current
    scan = ""
    if animated:
        scan = (
            f'<rect class="scan" x="0" y="0" width="110" height="100%" '
            f'fill="url(#scan-gradient)" clip-path="url(#world-clip-{suffix})"/>'
        )
    return f"""
    <path class="map-glow" d="{markup.outline}" fill="url(#map-glow)" stroke="#67e8f9" stroke-opacity=".42" stroke-width="2"/>
    <path d="{markup.outline}" fill="url(#ocean)" stroke="#67e8f9" stroke-opacity=".54" stroke-width="2"/>
    <g class="graticule" clip-path="url(#world-clip-{suffix})">{markup.graticule}</g>
    <g aria-hidden="true" clip-path="url(#world-clip-{suffix})">{markup.countries}{markup.tiny_countries}{scan}</g>
    <path id="life-route-{suffix}" class="route-base" d="{markup.route}"/>
    <path class="route-flow" d="{markup.route}"/>
    <path class="route-spark" d="{markup.route}"/>
    <circle class="origin-halo" cx="{_fmt(ox)}" cy="{_fmt(oy)}" r="13"/><circle class="origin-dot" cx="{_fmt(ox)}" cy="{_fmt(oy)}" r="6"/>
    <circle class="current-halo" cx="{_fmt(cx)}" cy="{_fmt(cy)}" r="13"/><circle class="current-dot" cx="{_fmt(cx)}" cy="{_fmt(cy)}" r="6"/>"""


def render_desktop(markup: MapMarkup, animated: bool) -> str:
    """Render the 1200x620 desktop journey atlas."""
    suffix = "desktop-motion" if animated else "desktop-static"
    title_suffix = "animated" if animated else "reduced-motion"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="620" viewBox="0 0 1200 620" role="img" aria-labelledby="title desc">
  <title id="title">Kevin Cusnir’s journey from San Cristóbal to Beersheba</title>
  <desc id="desc">A {title_suffix} Natural Earth world atlas with country outlines and tiny-state markers, highlighting Kevin’s birthplace in San Cristóbal, Venezuela, his current base in Beersheba, Israel, and Spanish, English and Hebrew communication.</desc>
  <!-- Natural Earth {VERSION} Admin-0 Countries and Tiny Countries; public domain: naturalearthdata.com -->
  <metadata>Natural Earth {VERSION}; {markup.country_count} country boundary features and {markup.tiny_count} tiny-country markers; public domain.</metadata>
{_defs(markup, animated, suffix)}
  <rect width="1200" height="620" rx="30" fill="url(#bg)"/><rect width="1200" height="620" rx="30" fill="url(#stars)"/>
  <text x="48" y="52" class="eyebrow">GLOBAL JOURNEY / COUNTRY ATLAS</text>
  <text x="48" y="96" class="title">From San Cristóbal to Beersheba</text>
  <text x="48" y="126" class="subtitle">Venezuelan roots · Israeli home · global collaboration</text>
  <g>{_map_layer(markup, suffix, animated)}</g>
  <text x="62" y="548" class="micro">COUNTRY OUTLINES WORLDWIDE · TINY STATES MARKED · ROUTE EMPHASIZED</text>
  <g>
    <rect x="790" y="156" width="362" height="122" rx="24" fill="#2d281b" stroke="#fbbf24" stroke-opacity=".72" stroke-width="2"/>
    <text x="824" y="188" class="card-kicker" fill="#fbbf24">BIRTHPLACE / VENEZUELA</text><text x="824" y="224" class="card-title">San Cristóbal</text><text x="824" y="252" class="card-copy">Spanish roots · first horizon</text>
    <path d="M971 285V326" stroke="url(#route)" stroke-width="4" stroke-dasharray="7 8"/><path d="M961 317L971 330 981 317" fill="none" stroke="#67e8f9" stroke-width="3"/>
    <rect x="790" y="338" width="362" height="122" rx="24" fill="#211d3d" stroke="#c4b5fd" stroke-opacity=".78" stroke-width="2"/>
    <text x="824" y="370" class="card-kicker" fill="#c4b5fd">CURRENT BASE / ISRAEL</text><text x="824" y="406" class="card-title">Beersheba</text><text x="824" y="434" class="card-copy">Negev home · present chapter</text>
    <rect x="790" y="492" width="104" height="42" rx="18" fill="#123a4b" stroke="#22d3ee"/><text x="842" y="518" text-anchor="middle" class="chip">ES · NATIVE</text>
    <rect x="906" y="492" width="112" height="42" rx="18" fill="#123f36" stroke="#34d399"/><text x="962" y="518" text-anchor="middle" class="chip">EN · ADV.</text>
    <rect x="1030" y="492" width="122" height="42" rx="18" fill="#2c2154" stroke="#a78bfa"/><text x="1091" y="518" text-anchor="middle" class="chip">HE · LOCAL</text>
  </g>
  <text x="48" y="592" class="micro">NATURAL EARTH 1:110m · PUBLIC-DOMAIN GEOGRAPHY</text><text x="1152" y="592" text-anchor="end" class="micro">LIRIOTH TELTANION · KEVIN CUSNIR</text>
  <rect x="1" y="1" width="1198" height="618" rx="29" fill="none" stroke="#7dd3fc" stroke-opacity=".2"/>
</svg>
"""


def render_mobile(markup: MapMarkup, animated: bool) -> str:
    """Render the 720x1180 mobile journey atlas."""
    suffix = "mobile-motion" if animated else "mobile-static"
    title_suffix = "animated" if animated else "reduced-motion"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="720" height="1180" viewBox="0 0 720 1180" role="img" aria-labelledby="title desc">
  <title id="title">Kevin Cusnir’s journey from San Cristóbal to Beersheba</title>
  <desc id="desc">A mobile {title_suffix} Natural Earth world atlas with country outlines and tiny-state markers, highlighting Kevin’s birthplace in San Cristóbal, Venezuela, his current base in Beersheba, Israel, and Spanish, English and Hebrew communication.</desc>
  <!-- Natural Earth {VERSION} Admin-0 Countries and Tiny Countries; public domain: naturalearthdata.com -->
  <metadata>Natural Earth {VERSION}; {markup.country_count} country boundary features and {markup.tiny_count} tiny-country markers; public domain.</metadata>
{_defs(markup, animated, suffix)}
  <rect width="720" height="1180" rx="32" fill="url(#bg)"/><rect width="720" height="1180" rx="32" fill="url(#stars)"/>
  <text x="42" y="54" class="eyebrow">GLOBAL JOURNEY / COUNTRY ATLAS</text>
  <text x="42" y="104" class="title">Two cities, one evolving story</text>
  <text x="42" y="138" class="subtitle">Venezuelan roots · Israeli home</text>
  <g>{_map_layer(markup, suffix, animated)}</g>
  <text x="52" y="520" class="micro">ALL COUNTRY OUTLINES · TINY STATES MARKED</text>
  <g>
    <rect x="48" y="558" width="624" height="154" rx="26" fill="#2d281b" stroke="#fbbf24" stroke-opacity=".78" stroke-width="2"/>
    <circle cx="96" cy="608" r="22" fill="#4b3a18" stroke="#fbbf24"/><text x="96" y="614" text-anchor="middle" class="chip">VE</text>
    <text x="136" y="596" class="card-kicker" fill="#fbbf24">BIRTHPLACE / VENEZUELA</text><text x="136" y="634" class="card-title">San Cristóbal</text><text x="136" y="670" class="card-copy">Spanish roots · first horizon</text>
    <path d="M360 718V764" stroke="url(#route)" stroke-width="5" stroke-dasharray="8 9"/><path d="M348 752L360 768 372 752" fill="none" stroke="#67e8f9" stroke-width="4"/>
    <rect x="48" y="776" width="624" height="154" rx="26" fill="#211d3d" stroke="#c4b5fd" stroke-opacity=".82" stroke-width="2"/>
    <circle cx="96" cy="826" r="22" fill="#35265e" stroke="#c4b5fd"/><text x="96" y="832" text-anchor="middle" class="chip">IL</text>
    <text x="136" y="814" class="card-kicker" fill="#c4b5fd">CURRENT BASE / ISRAEL</text><text x="136" y="852" class="card-title">Beersheba</text><text x="136" y="888" class="card-copy">Negev home · present chapter</text>
    <rect x="48" y="970" width="188" height="58" rx="22" fill="#123a4b" stroke="#22d3ee"/><text x="142" y="1005" text-anchor="middle" class="chip">ES · NATIVE</text>
    <rect x="266" y="970" width="188" height="58" rx="22" fill="#123f36" stroke="#34d399"/><text x="360" y="1005" text-anchor="middle" class="chip">EN · ADVANCED</text>
    <rect x="484" y="970" width="188" height="58" rx="22" fill="#2c2154" stroke="#a78bfa"/><text x="578" y="1005" text-anchor="middle" class="chip">HE · LOCAL</text>
  </g>
  <text x="42" y="1090" class="subtitle">Country boundaries frame the route.</text><text x="42" y="1122" class="card-copy">Clear communication carries it forward.</text>
  <text x="42" y="1152" class="micro">NATURAL EARTH 1:110m · PUBLIC DOMAIN</text>
  <rect x="1" y="1" width="718" height="1178" rx="31" fill="none" stroke="#7dd3fc" stroke-opacity=".2"/>
</svg>
"""


def _write_svg(path: Path, content: str) -> None:
    """Write and validate one LF-only SVG asset."""
    path.write_text(content, encoding="utf-8", newline="\n")
    ET.parse(path)
    size = path.stat().st_size
    if size > MAX_SVG_BYTES:
        raise ValueError(f"{path.name} is {size} bytes; maximum is {MAX_SVG_BYTES}.")


def main() -> int:
    """Generate and validate all responsive globe assets."""
    args = build_parser().parse_args()
    print(f"Natural Earth provenance: {VERSION}")
    for source in (COUNTRIES_SOURCE, TINY_COUNTRIES_SOURCE):
        print(f"- {source.filename}: sha256:{source.sha256}")
    countries = fetch_geojson(
        COUNTRIES_SOURCE,
        args.cache_dir,
        offline=args.offline,
        refresh_cache=args.refresh_cache,
    )
    tiny_countries = fetch_geojson(
        TINY_COUNTRIES_SOURCE,
        args.cache_dir,
        offline=args.offline,
        refresh_cache=args.refresh_cache,
    )
    desktop_map = build_map_markup(
        countries, tiny_countries, MapBox(x=48, y=166, width=700, height=350)
    )
    mobile_map = build_map_markup(
        countries, tiny_countries, MapBox(x=42, y=172, width=636, height=324)
    )
    outputs = {
        "world-globe-animated.svg": render_desktop(desktop_map, animated=True),
        "world-globe-static.svg": render_desktop(desktop_map, animated=False),
        "world-globe-mobile.svg": render_mobile(mobile_map, animated=True),
        "world-globe-mobile-static.svg": render_mobile(mobile_map, animated=False),
    }
    if not args.check:
        args.output_dir.mkdir(parents=True, exist_ok=True)
    failures = 0
    for filename, content in outputs.items():
        path = args.output_dir / filename
        if args.check:
            if not path.exists():
                print(f"Missing generated globe asset: {path}")
                failures += 1
                continue
            existing = path.read_text(encoding="utf-8")
            if existing != content:
                print(f"Generated globe asset is stale: {path}")
                failures += 1
            else:
                print(f"Current {filename}: {path.stat().st_size} bytes")
        else:
            _write_svg(path, content)
            print(f"Generated {filename}: {path.stat().st_size} bytes")
    print(
        "Coverage: "
        f"{desktop_map.country_count} country features + "
        f"{desktop_map.tiny_count} tiny-country markers [OK]"
    )
    if failures:
        print(f"Globe generation check failed: {failures} stale or missing asset(s).")
        return 1
    if args.check:
        print("Globe generation check passed without modifying assets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
