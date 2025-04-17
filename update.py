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

for name, style_cfg in style.items():
    print(f'generating image for {name}.svg')
    with open(f'img/{name}.svg', 'w', encoding="utf8") as output:
        output.write(
            neofetch_template.render(
                **style_cfg, 
                lines=render(get_sections(description)),
                ascii_lines=ascii.split('\n')
            )
        )





