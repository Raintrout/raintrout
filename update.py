import yaml

from mako.lookup import TemplateLookup

from helper import get_sections, render
from stars import *

template_lookup = TemplateLookup(
    directories=['templates'],
    strict_undefined=True,
    preprocessor=[lambda x: x.replace("\r\n", "\n")] # Avoids massive spacing on windows
)

ascii = render_sky(RA_CENTER, DEC_CENTER, FOV_RA_DEG, FOV_DEC_DEG,
               WIDTH, HEIGHT, MAG_LIMIT)
neofetch_template = template_lookup.get_template('neofetch.mako')
with open('templates/style.yaml', 'r') as style_file:
    style = yaml.safe_load(style_file.read())


with open('about.yaml', 'r') as about:
    description = yaml.safe_load(about.read())


def scale_mountain_height(path: str, scale: float, baseline: int = 530) -> str:
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

for name, style_cfg in style.items():
    print(f'generating image for {name}.svg')
    with open(f'img/{name}.svg', 'w', encoding="utf8") as output:
        render_style = dict(style_cfg)
        render_style["mountain_path"] = scale_mountain_height(
            render_style["mountain_path"],
            render_style.get("mountain_height_scale", 1.0),
        )
        output.write(
            neofetch_template.render(
                **render_style,
                lines=render(get_sections(description)),
                ascii_lines=ascii.split('\n')
            )
        )



