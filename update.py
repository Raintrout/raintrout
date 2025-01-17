import yaml

from mako.template import Template
from mako.lookup import TemplateLookup

template_lookup = TemplateLookup(
    directories=['templates'],
    strict_undefined=True,
    preprocessor=[lambda x: x.replace("\r\n", "\n")] # Avoids massive spacing on windows
)

neofetch_template = template_lookup.get_template('neofetch.mako')

with open('templates/style.yaml', 'r') as style_file:
    style = yaml.safe_load(style_file.read())

for name, style_cfg in style.items():
    print(f'generating image for {name}.svg')
    with open(f'img/{name}.svg', 'w', encoding="utf8") as output:
        output.write(neofetch_template.render(**style_cfg))