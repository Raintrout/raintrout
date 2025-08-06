import numpy as np
from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord
import astropy.units as u

# ─── CONFIGURATION ────────────────────────────────────────────────────────────

WIDTH, HEIGHT = 80, 24    # your ASCII grid size
WIDTH, HEIGHT = 40, 25
CHAR_ASPECT_RATIO = 2.0   # char_height / char_width
ZOOM = 0.21                # degrees of RA per column

RA_CENTER   = 56.750  # degrees
DEC_CENTER  = 24.117   # degrees

# compute fields of view
FOV_RA_DEG  = ZOOM * WIDTH
FOV_DEC_DEG = (ZOOM / CHAR_ASPECT_RATIO) * HEIGHT

MAG_LIMIT = 8.5        # faintest Vmag to include

# symbol → max Vmag
SYMBOLS = [
    ('o',  2.0),
    ('*',  3.5),
    ('+',  5.0),
    ('.',  MAG_LIMIT)
]


# ─── FUNCTIONS ────────────────────────────────────────────────────────────────

def fetch_stars(ra_center, dec_center, width_deg, height_deg, mag_limit):
    """Query Hipparcos for all stars in the rectangle around (ra,dec)."""
    v = Vizier(columns=['*'],  # grab everything, then pick the right RA/Dec
               column_filters={'Vmag': f'<{mag_limit}'},
               row_limit=-1)
    center = SkyCoord(ra_center, dec_center, unit=(u.deg, u.deg))
    tbls = v.query_region(center,
                          width=width_deg * u.deg,
                          height=height_deg * u.deg,
                          catalog='I/239/hip_main')
    if not tbls:
        raise RuntimeError("No data returned from Vizier.")
    table = tbls[0]

    # Find all RA/Dec-ish columns
    ra_cols  = [c for c in table.colnames if c.upper().startswith('RA')]
    dec_cols = [c for c in table.colnames if c.upper().startswith('DE')]

    # Prefer the true numeric ICRS columns if present
    for prefer in ('RAICRS', '_RA.icrs', 'RAJ2000'):
        if prefer in table.colnames:
            ra_col = prefer
            break
    else:
        ra_col = ra_cols[0]

    for prefer in ('DEICRS', '_DE.icrs', 'DEJ2000'):
        if prefer in table.colnames:
            dec_col = prefer
            break
    else:
        dec_col = dec_cols[0]

    # Check magnitude column
    if 'Vmag' not in table.colnames:
        raise KeyError("Couldn't find 'Vmag' column in the result.")

    return table, ra_col, dec_col

def map_stars_to_grid(table, ra_col, dec_col, ra_min, ra_max, dec_min, dec_max, w, h):
    """Convert each star’s RA/Dec into integer (x,y) on the ASCII grid."""
    ra  = table[ra_col].astype(float)
    dec = table[dec_col].astype(float)
    mag = table['Vmag'].astype(float)

    fx = (ra - ra_min) / (ra_max - ra_min)
    fy = (dec - dec_min) / (dec_max - dec_min)

    x = np.floor(fx * (w - 1)).astype(int)
    y = np.floor((1 - fy) * (h - 1)).astype(int)  # flip so Dec_max at top

    mask = (x >= 0) & (x < w) & (y >= 0) & (y < h)
    return x[mask], y[mask], mag[mask]

def choose_symbol(m):
    for sym, m_max in SYMBOLS:
        if m <= m_max:
            return sym
    return None

def render_sky(ra_center, dec_center, fov_ra, fov_dec, width, height, mag_limit):
    ra_min  = ra_center  - fov_ra  / 2
    ra_max  = ra_center  + fov_ra  / 2
    dec_min = dec_center - fov_dec / 2
    dec_max = dec_center + fov_dec / 2

    stars, ra_col, dec_col = fetch_stars(ra_center, dec_center, fov_ra, fov_dec, mag_limit)
    xs, ys, mags = map_stars_to_grid(stars, ra_col, dec_col,
                                     ra_min, ra_max, dec_min, dec_max,
                                     width, height)

    sky = [[' ' for _ in range(width)] for _ in range(height)]
    for x, y, m in zip(xs, ys, mags):
        sym = choose_symbol(m)
        if sym:
            sky[y][x] = sym

    return '\n'.join(''.join(row) for row in sky)

if __name__ == '__main__':
    sky = render_sky(RA_CENTER, DEC_CENTER, FOV_RA_DEG, FOV_DEC_DEG,
               WIDTH, HEIGHT, MAG_LIMIT)
    print(sky)
