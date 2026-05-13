def render_svg(
    *,
    svg_width: int,
    svg_height: int,
    font_size: int,
    style: str,
    background_color: str,
    border_radius: int,
    ascii_x: int,
    ascii_y: int,
    text_color: str,
    line_height: int,
    ascii_lines: list[str],
    mountain_path: str,
    mountain_color: str,
    work_timeline_svg: str,
    stats_x: int,
    stats_y: int,
    stats_text_color: str,
    lines: list[str],
    **_ignored: object,
) -> str:
    ascii_tspans = "\n".join(
        f'   <tspan x="{ascii_x}" y="{i * line_height + ascii_y}">{line}</tspan>'
        for i, line in enumerate(ascii_lines)
    )
    stat_lines = "\n".join(f'    {line}' for line in lines)
    return (
        "<?xml version='1.0' encoding='UTF-8'?>\n"
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'font-family="ConsolasFallback,Consolas,monospace" '
        f'width="{svg_width}px" height="{svg_height}px" '
        f'font-size="{font_size}px">\n'
        "<style>\n"
        f"{style}\n"
        "</style>\n"
        f'<rect width="{svg_width}px" height="{svg_height}px" '
        f'fill="{background_color}" rx="{border_radius}"/>\n'
        f'<text x="{ascii_x}" y="{ascii_y}" fill="{text_color}" class="ascii">\n'
        "<!-- image size (375,500) maybe add tarot card or something here in the future-->\n"
        f"{ascii_tspans}\n"
        "</text>\n"
        f'<path d="{mountain_path}" fill="{mountain_color}"/>\n'
        f"{work_timeline_svg}\n"
        f'<text x="{stats_x}" y="{stats_y}" fill="{stats_text_color}">\n'
        f"{stat_lines}\n"
        "</text>\n"
        "</svg>\n"
    )
