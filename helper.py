from dataclasses import dataclass
from typing import Iterator
from math import ceil

@dataclass
class Line:
    key: list[str]
    value: str

@dataclass
class Section:
    header: str
    lines: list[Line]

def split_value(value: str, line_length: int) -> list[str]:
    lines, line_index = [], [0]
    expected_lines = ceil(len(value)/line_length)
    for i in range(expected_lines-1):
        index = value.rfind(' ', line_index[i]+int(line_length*0.6), line_index[i]+int(line_length*0.8))
        if index == -1:
            index = value.rfind(' ', line_index[i], line_index[i]+line_length)
        line_index.append(index)
        lines.append(value[line_index[i]:index])
    lines.append(value[line_index[-1]:])
    return lines

def render_key(keys: list[str]) -> str:
        return '.'.join(f'<tspan class="key">{key}</tspan>' for key in keys)

def render(sections: Section, offset_x: int = 390, offset_y: int = 30, line_length: int = 60) -> Iterator[str]:
    for i, section in enumerate(sections):
        if i in [0]:
            yield f'<tspan x="{offset_x}" y="{offset_y}">{section.header}</tspan> {"—"*(line_length-1-len(section.header))}'
        else:
            yield f'<tspan x="{offset_x}" y="{offset_y}">- {section.header}</tspan> {"—"*(line_length-3-len(section.header))}'
        offset_y += 20

        for line in section.lines:
            key = '.'.join(line.key)
            value = line.value
            if len(value) + len(key) > line_length-10: # mulitline 
                for i, value in enumerate(split_value(value, line_length-5-len(key))):
                    if i == 0:
                        yield f'<tspan x="{offset_x}" y="{offset_y}" class="cc">. </tspan>{render_key(line.key)}:<tspan class="cc"> {"."*(line_length-5-len(key)-len(value))} </tspan><tspan class="value">{value}</tspan>'
                    else:
                        yield f'<tspan x="{offset_x}" y="{offset_y}" class="cc">. </tspan><tspan class="cc"> {"."*(line_length-5-len(value))} </tspan><tspan class="value">{value}</tspan>'
                    offset_y += 20
            else:
                yield f'<tspan x="{offset_x}" y="{offset_y}" class="cc">. </tspan>{render_key(line.key)}:<tspan class="cc"> {"."*(line_length-5-len(key)-len(value))} </tspan><tspan class="value">{value}</tspan>'
                offset_y += 20

        yield f'<tspan x="{offset_x}" y="{offset_y}" class="cc">. </tspan>'
        offset_y += 20
    
    while offset_y <= 510:
        yield f'<tspan x="{offset_x}" y="{offset_y}" class="cc">. </tspan>'
        offset_y += 20


def get_lines(section: dict, keys=[]) -> Iterator[Line]:
    for key, value in section.items():
            key_list = keys + [key]

            if isinstance(value, dict):
                yield from get_lines(value, keys=key_list)
            elif isinstance(value, list):
                yield Line(key_list, ', '.join(value))
            elif value is None:
                yield Line(key_list, "")
            else:
                yield Line(key_list, value)

def get_sections(about: dict) -> Iterator[Section]:
    for category, section in about.items():
        lines = list(get_lines(section))
        yield Section(category, lines)

