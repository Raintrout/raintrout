from dataclasses import dataclass
from math import ceil
from typing import Iterable, Iterator

LOW_CONTEXT_TRAILING_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}

@dataclass
class Line:
    key: list[str]
    value: str


@dataclass
class Section:
    header: str
    lines: list[Line]


def should_shift_boundary(previous_line: str, next_line: str) -> bool:
    previous_words = previous_line.split()
    next_words = next_line.split()
    if not previous_words or len(next_words) < 2:
        return False

    trailing_word = previous_words[-1].lower().strip(",.;:!?")
    return trailing_word in LOW_CONTEXT_TRAILING_WORDS


def split_value(value: str, line_length: int) -> list[str]:
    expected_lines = max(1, ceil(len(value) / line_length))
    words = value.split()

    if expected_lines == 1 or len(words) <= 1:
        return [value]

    lines = []
    current_words = []
    current_length = 0
    remaining_text_length = len(value)
    remaining_lines = expected_lines

    for word in words:
        separator_length = 1 if current_words else 0
        proposed_length = current_length + separator_length + len(word)
        target_length = remaining_text_length / remaining_lines

        if current_words and proposed_length > target_length:
            lines.append(' '.join(current_words))
            remaining_text_length -= current_length + 1
            remaining_lines -= 1
            current_words = [word]
            current_length = len(word)
            continue

        current_words.append(word)
        current_length = proposed_length

    if current_words:
        lines.append(' '.join(current_words))

    for index in range(len(lines) - 1):
        while should_shift_boundary(lines[index], lines[index + 1]):
            next_words = lines[index + 1].split()
            lines[index] = f"{lines[index]} {next_words[0]}"
            lines[index + 1] = ' '.join(next_words[1:])

    return lines


def render_key(keys: list[str]) -> str:
    return '.'.join(f'<tspan class="key">{key}</tspan>' for key in keys)


def render(
    sections: Iterable[Section],
    offset_x: int = 390,
    offset_y: int = 30,
    line_length: int = 60,
    line_height: int = 20,
    max_y: int = 510,
) -> Iterator[str]:
    for i, section in enumerate(sections):
        if i == 0:
            yield f'<tspan x="{offset_x}" y="{offset_y}">{section.header}</tspan> {"—"*(line_length-1-len(section.header))}'
        else:
            yield f'<tspan x="{offset_x}" y="{offset_y}">- {section.header}</tspan> {"—"*(line_length-3-len(section.header))}'
        offset_y += line_height

        for line in section.lines:
            key = '.'.join(line.key)
            value = line.value
            if len(value) + len(key) > line_length - 10:
                for i, value in enumerate(split_value(value, line_length-5-len(key))):
                    if i == 0:
                        yield f'<tspan x="{offset_x}" y="{offset_y}" class="cc">. </tspan>{render_key(line.key)}:<tspan class="cc"> {"."*(line_length-5-len(key)-len(value))} </tspan><tspan class="value">{value}</tspan>'
                    else:
                        yield f'<tspan x="{offset_x}" y="{offset_y}" class="cc">. </tspan><tspan class="cc"> {"."*(line_length-5-len(value))} </tspan><tspan class="value">{value}</tspan>'
                    offset_y += line_height
            else:
                yield f'<tspan x="{offset_x}" y="{offset_y}" class="cc">. </tspan>{render_key(line.key)}:<tspan class="cc"> {"."*(line_length-5-len(key)-len(value))} </tspan><tspan class="value">{value}</tspan>'
                offset_y += line_height

        yield f'<tspan x="{offset_x}" y="{offset_y}" class="cc">. </tspan>'
        offset_y += line_height
    
    while offset_y <= max_y:
        yield f'<tspan x="{offset_x}" y="{offset_y}" class="cc">. </tspan>'
        offset_y += line_height


def get_lines(section: dict, keys: list[str] | None = None) -> Iterator[Line]:
    keys = keys or []
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
        if str(category).startswith("_"):
            continue
        lines = list(get_lines(section))
        yield Section(category, lines)
