import yaml

STYLE = 'templates/style.yaml'
ASSETS = 'templates/neofetch.svg'


TEMPLATE = 'templates/README.md'
README = 'README.md'

with open(STYLE, 'r') as style_file:
    style = yaml.safe_load(style_file.read())

with open(ASSETS, 'r', encoding="utf8") as neofetch_template:
    template = neofetch_template.read()

    for name, style_cfg in style.items():
        print(f'generating image for {name}.svg')
        with open(f'img/{name}.svg', 'w', encoding="utf8") as output:
            output.write(
                str(template).replace('<--STYLE-->', style_cfg['style']).replace('<--BACKGROUND-->', style_cfg['background'])
            )




with open(TEMPLATE, 'r', encoding="utf8") as file:
    text = file.read()

with open(README, 'w', encoding="utf8") as file:
    file.write(text)