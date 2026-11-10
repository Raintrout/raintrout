"""Animated meteors over the ASCII sky, shown only while a meteor shower is active.

The SVG is regenerated daily, so we decide at build time which showers are active
and emit a few CSS-animated streaks that travel away from each shower's radiant.
"""
import math
import random
import sys
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Shower:
    name: str
    start: tuple[int, int]   # (month, day)
    peak: tuple[int, int]
    end: tuple[int, int]
    zhr: int
    radiant_ra: float        # degrees
    radiant_dec: float       # degrees


# Approximate IMO working-list values.
SHOWERS = [
    Shower("Quadrantids",        (12, 28), (1, 4),   (1, 12),  80, 230.0,  49.0),
    Shower("Lyrids",             (4, 14),  (4, 22),  (4, 30),  18, 271.0,  34.0),
    Shower("Eta Aquariids",      (4, 19),  (5, 6),   (5, 28),  50, 338.0,  -1.0),
    Shower("S. Delta Aquariids", (7, 12),  (7, 30),  (8, 23),  25, 340.0, -16.0),
    Shower("Perseids",           (7, 17),  (8, 12),  (8, 24), 100,  48.0,  58.0),
    Shower("Draconids",          (10, 6),  (10, 8),  (10, 10), 10, 262.0,  54.0),
    Shower("Orionids",           (10, 2),  (10, 21), (11, 7),  20,  95.0,  16.0),
    Shower("S. Taurids",         (9, 10),  (10, 10), (11, 20),  5,  32.0,   9.0),
    Shower("N. Taurids",         (10, 20), (11, 12), (12, 10),  5,  58.0,  22.0),
    Shower("Leonids",            (11, 6),  (11, 17), (11, 30), 15, 152.0,  22.0),
    Shower("Geminids",           (12, 4),  (12, 14), (12, 20), 150, 112.0,  33.0),
    Shower("Ursids",             (12, 17), (12, 22), (12, 26), 10, 217.0,  76.0),
]

EDGE_INTENSITY = 0.2
MAX_METEORS_PER_SHOWER = 6
# Radiants closer than this (deg) to the field center are projected directly into the
# image; farther ones use the true on-sky bearing.
NEAR_RADIANT_DEG = 10.0


def _window(shower: Shower, base_year: int) -> tuple[date, date, date]:
    start = date(base_year, *shower.start)
    end_year = base_year if shower.end >= shower.start else base_year + 1
    peak_year = base_year if shower.peak >= shower.start else base_year + 1
    return start, date(peak_year, *shower.peak), date(end_year, *shower.end)


def active_showers(today: date) -> list[tuple[Shower, float]]:
    """Return (shower, intensity in [EDGE_INTENSITY, 1]) for each shower active today."""
    active = []
    for shower in SHOWERS:
        for base_year in (today.year - 1, today.year):
            start, peak, end = _window(shower, base_year)
            if not (start <= today <= end):
                continue
            if today <= peak:
                span = (peak - start).days
                frac = (today - start).days / span if span else 1.0
            else:
                span = (end - peak).days
                frac = (end - today).days / span if span else 1.0
            active.append((shower, EDGE_INTENSITY + (1 - EDGE_INTENSITY) * frac))
            break
    return active


def _angular_separation(ra1, dec1, ra2, dec2) -> float:
    ra1, dec1, ra2, dec2 = map(math.radians, (ra1, dec1, ra2, dec2))
    cos_sep = (math.sin(dec1) * math.sin(dec2)
               + math.cos(dec1) * math.cos(dec2) * math.cos(ra1 - ra2))
    return math.degrees(math.acos(max(-1.0, min(1.0, cos_sep))))


def _bearing(ra1, dec1, ra2, dec2) -> float:
    """Position angle (radians, east of north) of point 2 as seen from point 1."""
    ra1, dec1, ra2, dec2 = map(math.radians, (ra1, dec1, ra2, dec2))
    d_ra = ra2 - ra1
    return math.atan2(
        math.sin(d_ra) * math.cos(dec2),
        math.cos(dec1) * math.sin(dec2) - math.sin(dec1) * math.cos(dec2) * math.cos(d_ra),
    )


def render_meteors(
    today: date,
    *,
    box: tuple[float, float, float, float],
    color: str,
    ra_center: float,
    dec_center: float,
    fov_ra: float,
    fov_dec: float,
) -> str:
    """SVG snippet with animated meteors, or "" when no shower is active.

    box is (x0, y0, x1, y1) in SVG pixels covering the ASCII sky. The image maps RA
    increasing to the right and Dec increasing upward (see stars.map_stars_to_grid).
    """
    showers = active_showers(today)
    if not showers:
        return ""

    rng = random.Random(today.toordinal())
    x0, y0, x1, y1 = box
    width, height = x1 - x0, y1 - y0

    meteors = []
    for shower, intensity in showers:
        count = max(1, min(MAX_METEORS_PER_SHOWER, round(shower.zhr * intensity / 20)))
        sep = _angular_separation(ra_center, dec_center, shower.radiant_ra, shower.radiant_dec)
        if sep < NEAR_RADIANT_DEG:
            d_ra = (shower.radiant_ra - ra_center + 180) % 360 - 180
            rad_x = x0 + (0.5 + d_ra / fov_ra) * width
            rad_y = y0 + (0.5 - (shower.radiant_dec - dec_center) / fov_dec) * height
            fixed_dir = None
        else:
            pa = _bearing(ra_center, dec_center, shower.radiant_ra, shower.radiant_dec)
            # Radiant lies toward (sin pa, -cos pa) on screen; meteors travel away from it.
            fixed_dir = (-math.sin(pa), math.cos(pa))

        for _ in range(count):
            sx = rng.uniform(x0 + 20, x1 - 20)
            sy = rng.uniform(y0 + 10, y0 + 0.7 * height)
            if fixed_dir is None:
                dx, dy = sx - rad_x, sy - rad_y
                norm = math.hypot(dx, dy) or 1.0
                ux, uy = dx / norm, dy / norm
            else:
                # Small jitter so parallel streaks don't look mechanical.
                jitter = math.radians(rng.uniform(-8, 8))
                fx, fy = fixed_dir
                ux = fx * math.cos(jitter) - fy * math.sin(jitter)
                uy = fx * math.sin(jitter) + fy * math.cos(jitter)
            meteors.append((sx, sy, ux, uy))

    defs, groups, keyframes = [], [], []
    for i, (sx, sy, ux, uy) in enumerate(meteors):
        tail = rng.uniform(40, 90)
        travel = rng.uniform(60, 120)
        duration = rng.uniform(10, 25)
        delay = rng.uniform(0, duration)
        visible_pct = 100 * rng.uniform(0.6, 1.0) / duration
        tx, ty = -tail * ux, -tail * uy

        defs.append(
            f'<linearGradient id="meteorGrad{i}" gradientUnits="userSpaceOnUse" '
            f'x1="{tx:.1f}" y1="{ty:.1f}" x2="0" y2="0">'
            f'<stop offset="0" stop-color="{color}" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity="1"/>'
            f'</linearGradient>'
        )
        end = f"translate({travel * ux:.1f}px, {travel * uy:.1f}px)"
        keyframes.append(
            f"@keyframes meteor{i} {{"
            f" 0% {{transform: translate(0px, 0px); opacity: 0}}"
            f" {visible_pct * 0.15:.2f}% {{opacity: 1}}"
            f" {visible_pct:.2f}% {{transform: {end}; opacity: 0}}"
            f" 100% {{transform: {end}; opacity: 0}} }}"
        )
        groups.append(
            f'<g transform="translate({sx:.1f} {sy:.1f})">'
            f'<g class="meteor" style="animation: meteor{i} {duration:.1f}s linear '
            f'{delay:.1f}s infinite both">'
            f'<line x1="{tx:.1f}" y1="{ty:.1f}" x2="0" y2="0" '
            f'stroke="url(#meteorGrad{i})" stroke-width="1.5" stroke-linecap="round"/>'
            f'</g></g>'
        )

    names = ", ".join(s.name for s, _ in showers)
    style = "\n".join(keyframes) + (
        "\n.meteor {opacity: 0;}"
        "\n@media (prefers-reduced-motion: reduce) {.meteor {animation: none !important;}}"
    )
    return (
        f"<!-- meteors: {names} -->\n"
        f"<style>\n{style}\n</style>\n"
        f"<defs>\n" + "\n".join(defs) + "\n</defs>\n"
        + "\n".join(groups)
    )


if __name__ == "__main__":
    from stars import DEC_CENTER, FOV_DEC_DEG, FOV_RA_DEG, RA_CENTER

    day = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    print(render_meteors(
        day, box=(15, 15, 405, 470), color="#e6edf3",
        ra_center=RA_CENTER, dec_center=DEC_CENTER,
        fov_ra=FOV_RA_DEG, fov_dec=FOV_DEC_DEG,
    ))
