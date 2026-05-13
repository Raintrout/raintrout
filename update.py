import calendar
from copy import deepcopy
from datetime import date, datetime

import yaml
from mako.lookup import TemplateLookup

from renderer import render
from sections import get_sections
from stars import (
    DEC_CENTER,
    FOV_DEC_DEG,
    FOV_RA_DEG,
    HEIGHT,
    MAG_LIMIT,
    RA_CENTER,
    WIDTH,
    render_sky,
)

DEFAULT_LAYOUT = {
    "ascii_x": 15,
    "ascii_y": 30,
    "border_radius": 15,
    "font_size": 16,
    "line_height": 20,
    "stats_text_color": "#c9d1d9",
    "stats_x": 390,
    "stats_y": 30,
    "svg_height": 530,
    "svg_width": 985,
}


def scale_mountain_height(path: str, scale: float, baseline: int = 530) -> str:
    # Only supports the M/L/Z subset used by templates/style.yaml.
    tokens = path.split()
    transformed = []
    command = None
    coord_index = 0

    for token in tokens:
        if token in {"M", "L", "Z"}:
            command = token
            coord_index = 0
            transformed.append(token)
            continue

        if command in {"M", "L"} and coord_index % 2 == 1:
            y_value = float(token)
            adjusted = baseline - ((baseline - y_value) * scale)
            transformed.append(str(int(round(adjusted))))
        else:
            transformed.append(token)

        coord_index += 1

    return " ".join(transformed)


def parse_config_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


def format_uptime(birthdate: date, today: date | None = None) -> str:
    today = today or date.today()

    years = today.year - birthdate.year
    months = today.month - birthdate.month
    days = today.day - birthdate.day

    if days < 0:
        prev_month = today.month - 1 if today.month > 1 else 12
        prev_month_year = today.year if today.month > 1 else today.year - 1
        days += calendar.monthrange(prev_month_year, prev_month)[1]
        months -= 1

    if months < 0:
        months += 12
        years -= 1

    return f"{years}y {months:02}mo {days:02}d"


def hydrate_description(raw_description: dict) -> dict:
    hydrated = deepcopy(raw_description)
    config = hydrated.get("_config", {})
    birthdate = config.get("birthdate")

    if birthdate:
        profile_name = next(
            (key for key in hydrated.keys() if not str(key).startswith("_")),
            None,
        )
        if profile_name and hydrated[profile_name].get("Uptime") == "auto":
            hydrated[profile_name]["Uptime"] = format_uptime(
                parse_config_date(birthdate)
            )

    return hydrated


def compute_stats_line_length(svg_width: int, stats_x: int, font_size: int) -> int:
    available_width = max(0, svg_width - stats_x - 15)
    monospace_char_width = font_size * 0.61
    return max(20, int(available_width / monospace_char_width))


def build_render_style(style_cfg: dict, hydrated_description: dict) -> dict:
    render_style = {**DEFAULT_LAYOUT, **style_cfg}
    render_style["stats_line_length"] = style_cfg.get(
        "stats_line_length",
        compute_stats_line_length(
            render_style["svg_width"],
            render_style["stats_x"],
            render_style["font_size"],
        ),
    )
    render_style["mountain_path"] = scale_mountain_height(
        render_style["mountain_path"],
        render_style.get("mountain_height_scale", 1.0),
        baseline=render_style["svg_height"],
    )
    lines, overlays = render(
        get_sections(hydrated_description),
        offset_x=render_style["stats_x"],
        offset_y=render_style["stats_y"],
        line_length=render_style["stats_line_length"],
        line_height=render_style["line_height"],
        max_y=render_style["svg_height"] - render_style["line_height"],
        work_timeline_line_color=render_style["work_timeline_line_color"],
    )
    render_style["lines"] = lines
    render_style["work_timeline_svg"] = "\n".join(overlays)
    return render_style


def main() -> None:
    template_lookup = TemplateLookup(
        directories=['templates'],
        strict_undefined=True,
        preprocessor=[lambda x: x.replace("\r\n", "\n")],  # Avoids massive spacing on windows
    )
    neofetch_template = template_lookup.get_template('neofetch.mako')

    with open('templates/style.yaml', 'r') as style_file:
        style = yaml.safe_load(style_file.read())

    with open('about.yaml', 'r') as about_file:
        description = yaml.safe_load(about_file.read())

    hydrated_description = hydrate_description(description)
    ascii_art = render_sky(
        RA_CENTER, DEC_CENTER, FOV_RA_DEG, FOV_DEC_DEG,
        WIDTH, HEIGHT, MAG_LIMIT,
    )

    for name, style_cfg in style.items():
        print(f'generating image for {name}.svg')
        render_style = build_render_style(style_cfg, hydrated_description)
        with open(f'img/{name}.svg', 'w', encoding="utf8") as output:
            output.write(
                neofetch_template.render(
                    **render_style,
                    ascii_lines=ascii_art.split('\n'),
                )
            )


if __name__ == '__main__':
    main()
