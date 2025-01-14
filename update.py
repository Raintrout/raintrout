from datetime import datetime

TEMPLATE = 'templates/README.md'
README = 'README.md'

with open(TEMPLATE, 'r', encoding="utf8") as file:
    text = file.read()

text = text.replace('<!--TIME-->', f'{datetime.now()}')

with open(README, 'w', encoding="utf8") as file:
    file.write(text)